#include <iostream>
#include <vector>
#include <string>
#include <cstring>
#include <unistd.h>
#include <fcntl.h>
#include <sys/epoll.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include "ThreadPool.hpp"

// 定義常數
const int MAX_EVENTS = 1024;
const int PORT = 8080;
const int THREAD_COUNT = 4;

// 設定 Socket 為非阻塞模式 (Non-blocking)
int setNonBlocking(int fd) {
    int flags = fcntl(fd, F_GETFL, 0);
    if (flags == -1) return -1;
    return fcntl(fd, F_SETFL, flags | O_NONBLOCK);
}

// 修改 epoll 事件（重新註冊 ONESHOT）
void mod_event(int epoll_fd, int fd, uint32_t ev) {
    struct epoll_event event;
    event.data.fd = fd;
    event.events = ev | EPOLLET | EPOLLONESHOT | EPOLLRDHUP;
    epoll_ctl(epoll_fd, EPOLL_CTL_MOD, fd, &event);
}

// 處理 HTTP 請求的工作邏輯 (由 Thread Pool 執行)
void handle_client_request(int client_fd, int epoll_fd) {
    char buffer[4096];
    // 在非阻塞模式下，簡化處理：讀取請求（此處不處理複雜解析，僅為清空緩衝區）
    ssize_t bytes_read = recv(client_fd, buffer, sizeof(buffer), 0);
    
    if (bytes_read > 0) {
        std::cout << "[Thread " << std::this_thread::get_id() << "] Handling request on FD: " << client_fd << std::endl;

        // 構造一個簡單的 HTTP 回應
        std::string html_content = "<html><body><h1>Hello from High-Performance C++ Server</h1><p>Powered by epoll & Thread Pool.</p></body></html>";
        std::string http_response = 
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html; charset=UTF-8\r\n"
            "Content-Length: " + std::to_string(html_content.size()) + "\r\n"
            "Connection: close\r\n"
            "\r\n" + html_content;

        send(client_fd, http_response.c_str(), http_response.size(), 0);
    }

    // 關閉連接（符合 HTTP/1.1 短連接示例）
    close(client_fd);
}

int main() {
    // 1. 建立監聽 Socket
    int listen_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (listen_fd == -1) { perror("socket failed"); return 1; }

    // 設定端口復用
    int opt = 1;
    setsockopt(listen_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(listen_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        perror("bind failed"); return 1;
    }

    if (listen(listen_fd, 128) < 0) {
        perror("listen failed"); return 1;
    }

    setNonBlocking(listen_fd);
    std::cout << "Server started on port " << PORT << "..." << std::endl;

    // 2. 初始化 epoll
    int epoll_fd = epoll_create1(0);
    if (epoll_fd == -1) { perror("epoll_create failed"); return 1; }

    struct epoll_event event;
    event.data.fd = listen_fd;
    event.events = EPOLLIN | EPOLLET; // 監聽 Socket 使用邊緣觸發
    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, listen_fd, &event);

    // 3. 初始化執行緒池
    ThreadPool pool(THREAD_COUNT);

    struct epoll_event events[MAX_EVENTS];

    // 4. 事件循環 (Reactor Main Loop)
    while (true) {
        int n = epoll_wait(epoll_fd, events, MAX_EVENTS, -1);
        for (int i = 0; i < n; i++) {
            int fd = events[i].data.fd;

            // 處理新連線
            if (fd == listen_fd) {
                struct sockaddr_in client_addr;
                socklen_t client_len = sizeof(client_addr);
                int client_fd = accept(listen_fd, (struct sockaddr*)&client_addr, &client_len);
                
                if (client_fd > 0) {
                    setNonBlocking(client_fd);
                    // 註冊新 Socket 到 epoll，使用 EPOLLONESHOT 確保執行緒安全
                    struct epoll_event ev;
                    ev.data.fd = client_fd;
                    ev.events = EPOLLIN | EPOLLET | EPOLLONESHOT | EPOLLRDHUP;
                    epoll_ctl(epoll_fd, EPOLL_CTL_ADD, client_fd, &ev);
                }
            } 
            // 處理讀取事件（現有連線有資料進來）
            else if (events[i].events & EPOLLIN) {
                // 將任務丟進 Thread Pool
                // 注意：一旦任務被丟出，該 FD 就不會再被 epoll 觸發（因為 ONESHOT），
                // 直到我們手動 mod_event 重新註冊。
                pool.enqueue([fd, epoll_fd] {
                    handle_client_request(fd, epoll_fd);
                });
            }
            // 處理斷開連接或錯誤
            else if (events[i].events & (EPOLLRDHUP | EPOLLHUP | EPOLLERR)) {
                close(fd);
            }
        }
    }

    close(listen_fd);
    return 0;
}