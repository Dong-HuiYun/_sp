# 第五章：檔案系統與輸入輸出

## 5.1 檔案系統概述

檔案系統是作業系統用於組織、儲存和檢索資料的機制。它提供了檔案和目錄的抽象，使得使用者可以方便地管理資料。

### 5.1.1 檔案的概念

檔案是具有名稱的相關資訊集合，在作業系統中作為基本的儲存單位。

```c
// 檔案的基本屬性結構
typedef struct {
    char name[256];              // 檔案名稱
    char path[1024];             // 完整路徑
    unsigned long size;          // 檔案大小
    time_t created;              // 創建時間
    time_t modified;            // 修改時間
    time_t accessed;             // 存取時間
    unsigned short permissions;  // 權限
    unsigned int attributes;     // 屬性
    unsigned long inode;         // inode 號碼
} FileInfo;

typedef enum {
    FILE_TYPE_REGULAR,           // 普通檔案
    FILE_TYPE_DIRECTORY,         // 目錄
    FILE_TYPE_SYMLINK,           // 符號連結
    FILE_TYPE_BLOCK,             // 區塊裝置
    FILE_TYPE_CHAR,              // 字元裝置
    FILE_TYPE_FIFO,              // FIFO/管道
    FILE_TYPE_SOCKET             // 插槽
} FileType;
```

### 5.1.2 常見的檔案系統類型

```
┌─────────────────────────────────────────────┐
│           檔案系統類型                       │
├─────────────┬─────────────┬────────────────┤
│  傳統檔案系統 │  日誌檔案系統 │  網路檔案系統  │
├─────────────┼─────────────┼────────────────┤
│    FAT      │    ext3     │      NFS       │
│    NTFS     │    ext4     │      SMB       │
│    FAT32    │    XFS      │      CIFS      │
│    exFAT    │    Btrfs    │      FTP       │
│    HFS+     │    ZFS      │      WebDAV    │
└─────────────┴─────────────┴────────────────┘
```

## 5.2 檔案系統架構

### 5.2.1 層次結構

```
┌─────────────────────────────────────────┐
│           應用程式                       │
├─────────────────────────────────────────┤
│         標準程式庫 (fopen, fread...)     │
├─────────────────────────────────────────┤
│         系統呼叫介面 (open, read...)     │
├─────────────────────────────────────────┤
│         虛擬檔案系統 (VFS)              │
├───────────────┬─────────────────────────┤
│   網路檔案系統 │     本地檔案系統        │
│     (NFS)     │  (ext4, NTFS, FAT...)   │
├───────────────┴─────────────────────────┤
│         區塊層 (Block Layer)            │
├─────────────────────────────────────────┤
│         裝置驅動程式                     │
├─────────────────────────────────────────┤
│         實體硬體                         │
└─────────────────────────────────────────┘
```

### 5.2.2 inode 結構

在 Unix 類型的檔案系統中，inode 是儲存檔案元資料的核心結構。

```c
typedef struct inode {
    unsigned long inode_num;      // inode 號碼
    unsigned short mode;          // 檔案類型和權限
    unsigned short uid;           // 擁有者 UID
    unsigned long size;           // 檔案大小（位元組）
    unsigned long blocks;         // 分配的區塊數
    unsigned long atime;          // 最後存取時間
    unsigned long mtime;          // 最後修改時間
    unsigned long ctime;          // inode 修改時間
    unsigned long dtime;          // 刪除時間
    unsigned short gid;           // 擁有者 GID
    unsigned short links_count;   // 硬連結數
    unsigned long blocks[15];     // 直接和間接區塊指標
    unsigned long indirect;       // 單間接區塊指標
    unsigned long double_indirect;// 雙間接區塊指標
    unsigned long triple_indirect;// 三間接區塊指標
    unsigned int flags;           // inode 標誌
    unsigned int osd1;            // 作業系統特定
} Inode;

// 區塊指標示意
// blocks[0-11]: 12 個直接區塊指標
// blocks[12]: 單間接區塊指標
// blocks[13]: 雙間接區塊指標
// blocks[14]: 三間接區塊指標
```

## 5.3 標準輸入輸出程式設計

### 5.3.1 基本檔案操作

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int basic_file_operations(void) {
    FILE *file;
    
    // 寫入檔案
    file = fopen("example.txt", "w");
    if (file == NULL) {
        fprintf(stderr, "Failed to open file for writing\n");
        return -1;
    }
    
    fprintf(file, "Hello, File System!\n");
    fprintf(file, "Line 2: System Programming\n");
    fprintf(file, "Line 3: File I/O operations\n");
    
    fclose(file);
    
    // 讀取檔案
    file = fopen("example.txt", "r");
    if (file == NULL) {
        fprintf(stderr, "Failed to open file for reading\n");
        return -1;
    }
    
    char buffer[256];
    while (fgets(buffer, sizeof(buffer), file) != NULL) {
        printf("%s", buffer);
    }
    
    fclose(file);
    
    return 0;
}

int binary_file_operations(void) {
    typedef struct {
        char name[50];
        int age;
        float salary;
    } Employee;
    
    Employee emp1 = {"John Doe", 30, 50000.0};
    Employee emp2 = {"Jane Smith", 28, 55000.0};
    
    // 寫入二進制檔案
    FILE *file = fopen("employees.dat", "wb");
    if (file == NULL) {
        return -1;
    }
    
    fwrite(&emp1, sizeof(Employee), 1, file);
    fwrite(&emp2, sizeof(Employee), 1, file);
    
    fclose(file);
    
    // 讀取二進制檔案
    file = fopen("employees.dat", "rb");
    if (file == NULL) {
        return -1;
    }
    
    Employee read_emp;
    while (fread(&read_emp, sizeof(Employee), 1, file) == 1) {
        printf("Name: %s, Age: %d, Salary: %.2f\n",
               read_emp.name, read_emp.age, read_emp.salary);
    }
    
    fclose(file);
    
    return 0;
}
```

### 5.3.2 格式化輸入輸出

```c
#include <stdio.h>

int formatted_io_example(void) {
    FILE *file = fopen("data.csv", "w");
    if (file == NULL) return -1;
    
    fprintf(file, "ID,Name,Age,Score\n");
    fprintf(file, "%d,%s,%d,%.2f\n", 1, "Alice", 20, 95.5);
    fprintf(file, "%d,%s,%d,%.2f\n", 2, "Bob", 22, 88.3);
    fprintf(file, "%d,%s,%d,%.2f\n", 3, "Charlie", 21, 92.0);
    
    fclose(file);
    
    file = fopen("data.csv", "r");
    if (file == NULL) return -1;
    
    int id, age;
    char name[50];
    float score;
    
    char header[100];
    fgets(header, sizeof(header), file);
    
    while (fscanf(file, "%d,%49[^,],%d,%f\n", &id, name, &age, &score) == 4) {
        printf("ID: %d, Name: %s, Age: %d, Score: %.2f\n",
               id, name, age, score);
    }
    
    fclose(file);
    
    return 0;
}
```

## 5.4 系統呼叫

### 5.4.1 Linux 檔案系統呼叫

```c
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>

int linux_file_operations(void) {
    int fd;
    ssize_t bytes_written, bytes_read;
    char buffer[1024];
    
    // 開啟檔案
    fd = open("test.txt", O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd == -1) {
        perror("open");
        return -1;
    }
    
    // 寫入資料
    const char *msg = "Hello from Linux system calls!\n";
    bytes_written = write(fd, msg, strlen(msg));
    printf("Wrote %zd bytes\n", bytes_written);
    
    // 關閉檔案
    close(fd);
    
    // 重新開啟以讀取
    fd = open("test.txt", O_RDONLY);
    if (fd == -1) {
        perror("open");
        return -1;
    }
    
    // 讀取資料
    bytes_read = read(fd, buffer, sizeof(buffer) - 1);
    if (bytes_read > 0) {
        buffer[bytes_read] = '\0';
        printf("Read: %s", buffer);
    }
    
    close(fd);
    
    return 0;
}
```

### 5.4.2 檔案描述符操作

```c
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int file_descriptor_operations(void) {
    int fd1, fd2;
    
    fd1 = open("file1.txt", O_RDWR | O_CREAT, 0644);
    if (fd1 == -1) {
        perror("open file1");
        return -1;
    }
    
    write(fd1, "Original content", 16);
    
    // 複製檔案描述符
    fd2 = dup(fd1);
    if (fd2 == -1) {
        perror("dup");
        close(fd1);
        return -1;
    }
    
    // 使用 dup2 重定向
    int saved_stdout = dup(STDOUT_FILENO);
    
    if (dup2(fd2, STDOUT_FILENO) == -1) {
        perror("dup2");
        return -1;
    }
    
    printf("This goes to file1.txt\n");
    fflush(stdout);
    
    dup2(saved_stdout, STDOUT_FILENO);
    
    printf("This goes to terminal\n");
    
    close(fd1);
    close(fd2);
    
    return 0;
}

int file_status(void) {
    struct stat file_stat;
    
    if (stat("example.txt", &file_stat) == -1) {
        perror("stat");
        return -1;
    }
    
    printf("File: example.txt\n");
    printf("Size: %ld bytes\n", (long)file_stat.st_size);
    printf("Permissions: %o\n", file_stat.st_mode & 0777);
    printf("Last modified: %ld\n", (long)file_stat.st_mtime);
    printf("Last accessed: %ld\n", (long)file_stat.st_atime);
    printf(" inode: %ld\n", (long)file_stat.st_ino);
    
    if (S_ISREG(file_stat.st_mode)) {
        printf("Type: Regular file\n");
    } else if (S_ISDIR(file_stat.st_mode)) {
        printf("Type: Directory\n");
    }
    
    return 0;
}
```

### 5.4.3 檔案鎖定

```c
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>

int file_locking_example(void) {
    int fd = open("locked_file.txt", O_RDWR | O_CREAT, 0644);
    if (fd == -1) {
        perror("open");
        return -1;
    }
    
    struct flock fl;
    
    fl.l_type = F_WRLCK;     // 寫入鎖
    fl.l_whence = SEEK_SET;
    fl.l_start = 0;
    fl.l_len = 0;             // 0 表示鎖定整個檔案
    fl.l_pid = getpid();
    
    printf("Trying to acquire write lock...\n");
    
    if (fcntl(fd, F_SETLKW, &fl) == -1) {
        perror("fcntl");
        close(fd);
        return -1;
    }
    
    printf("Lock acquired! Doing work...\n");
    
    for (int i = 0; i < 5; i++) {
        printf("Working... %d\n", i + 1);
        sleep(1);
    }
    
    fl.l_type = F_UNLCK;
    
    if (fcntl(fd, F_SETLK, &fl) == -1) {
        perror("fcntl unlock");
    }
    
    printf("Lock released!\n");
    
    close(fd);
    
    return 0;
}

int non_blocking_lock(void) {
    int fd = open("locked_file.txt", O_RDWR);
    if (fd == -1) {
        perror("open");
        return -1;
    }
    
    struct flock fl;
    fl.l_type = F_WRLCK;
    fl.l_whence = SEEK_SET;
    fl.l_start = 0;
    fl.l_len = 0;
    fl.l_pid = getpid();
    
    if (fcntl(fd, F_SETLK, &fl) == -1) {
        printf("Lock is already held by another process\n");
    } else {
        printf("Lock acquired successfully\n");
        sleep(5);
        fl.l_type = F_UNLCK;
        fcntl(fd, F_SETLK, &fl);
    }
    
    close(fd);
    
    return 0;
}
```

## 5.5 目錄操作

### 5.5.1 目錄遍歷

```c
#include <dirent.h>
#include <stdio.h>
#include <string.h>

int list_directory(const char *path) {
    DIR *dir = opendir(path);
    if (dir == NULL) {
        perror("opendir");
        return -1;
    }
    
    struct dirent *entry;
    
    while ((entry = readdir(dir)) != NULL) {
        printf("%s", entry->d_name);
        
        switch (entry->d_type) {
            case DT_REG:
                printf(" [File]");
                break;
            case DT_DIR:
                printf(" [Dir]");
                break;
            case DT_LNK:
                printf(" [Link]");
                break;
            default:
                printf(" [Unknown]");
        }
        printf("\n");
    }
    
    closedir(dir);
    
    return 0;
}

int recursive_directory_list(const char *path, int depth) {
    DIR *dir = opendir(path);
    if (dir == NULL) {
        return -1;
    }
    
    struct dirent *entry;
    char full_path[1024];
    
    while ((entry = readdir(dir)) != NULL) {
        if (strcmp(entry->d_name, ".") == 0 ||
            strcmp(entry->d_name, "..") == 0) {
            continue;
        }
        
        for (int i = 0; i < depth; i++) {
            printf("  ");
        }
        printf("%s\n", entry->d_name);
        
        if (entry->d_type == DT_DIR) {
            snprintf(full_path, sizeof(full_path), "%s/%s", path, entry->d_name);
            recursive_directory_list(full_path, depth + 1);
        }
    }
    
    closedir(dir);
    
    return 0;
}
```

### 5.5.2 目錄創建與刪除

```c
#include <sys/stat.h>
#include <sys/types.h>
#include <unistd.h>

int directory_operations(void) {
    const char *dir_path = "new_directory";
    
    // 創建目錄
    if (mkdir(dir_path, 0755) == -1) {
        perror("mkdir");
    } else {
        printf("Directory '%s' created successfully\n", dir_path);
    }
    
    // 創建嵌套目錄
    const char *nested_path = "parent/child/grandchild";
    if (mkdir(nested_path, 0755) == -1) {
        perror("mkdir nested");
    }
    
    // 使用 mkdir -p 功能（遞迴創建）
    char path[1024];
    char *token;
    strcpy(path, nested_path);
    
    for (token = strtok(path, "/"); token != NULL; token = strtok(NULL, "/")) {
        static char current_path[1024] = "";
        strcat(current_path, token);
        strcat(current_path, "/");
        mkdir(current_path, 0755);
    }
    
    // 刪除空目錄
    if (rmdir(dir_path) == -1) {
        perror("rmdir");
    } else {
        printf("Directory '%s' removed successfully\n", dir_path);
    }
    
    return 0;
}
```

## 5.6 緩衝區管理

### 5.6.1 緩衝區類型

```c
#include <stdio.h>
#include <string.h>

typedef enum {
    BUFFER_FULL,      // 全緩衝
    BUFFER_LINE,      // 行緩衝
    BUFFER_NONE      // 無緩衝
} BufferType;

typedef struct {
    char *buffer;
    size_t size;
    size_t position;
    size_t capacity;
    BufferType type;
    FILE *file;
} Buffer;

Buffer* buffer_create(size_t capacity, BufferType type, FILE *file) {
    Buffer *buf = (Buffer*)malloc(sizeof(Buffer));
    buf->buffer = (char*)malloc(capacity);
    buf->capacity = capacity;
    buf->size = 0;
    buf->position = 0;
    buf->type = type;
    buf->file = file;
    return buf;
}

int buffer_flush(Buffer *buf) {
    if (buf->size > 0 && buf->file != NULL) {
        size_t written = fwrite(buf->buffer, 1, buf->size, buf->file);
        buf->size = 0;
        return (written == buf->size) ? 0 : -1;
    }
    return 0;
}

int buffer_write(Buffer *buf, const char *data, size_t len) {
    for (size_t i = 0; i < len; i++) {
        if (buf->size >= buf->capacity) {
            if (buffer_flush(buf) != 0) {
                return -1;
            }
        }
        
        buf->buffer[buf->size++] = data[i];
        
        if (buf->type == BUFFER_LINE && data[i] == '\n') {
            buffer_flush(buf);
        }
    }
    
    return 0;
}

void buffer_destroy(Buffer *buf) {
    buffer_flush(buf);
    free(buf->buffer);
    free(buf);
}
```

### 5.6.2 setvbuf 範例

```c
#include <stdio.h>

int custom_buffering(void) {
    FILE *file = fopen("buffered.txt", "w");
    if (file == NULL) {
        return -1;
    }
    
    char buffer[4096];
    
    setvbuf(file, buffer, _IOFBF, sizeof(buffer));
    
    fprintf(file, "This is line 1\n");
    fprintf(file, "This is line 2\n");
    fprintf(file, "This is line 3\n");
    
    fflush(file);
    
    fclose(file);
    
    file = fopen("unbuffered.txt", "w");
    if (file == NULL) {
        return -1;
    }
    
    setvbuf(file, NULL, _IONBF, 0);
    
    fprintf(file, "Immediate write\n");
    
    fclose(file);
    
    return 0;
}
```

## 5.7 記憶體映射檔案

### 5.7.1 mmap 的使用

```c
#include <sys/mman.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

int memory_mapped_file_write(const char *filename, const char *data, size_t size) {
    int fd = open(filename, O_RDWR | O_CREAT | O_TRUNC, 0644);
    if (fd == -1) {
        perror("open");
        return -1;
    }
    
    if (ftruncate(fd, size) == -1) {
        perror("ftruncate");
        close(fd);
        return -1;
    }
    
    void *mapped = mmap(NULL, size, PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    if (mapped == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return -1;
    }
    
    memcpy(mapped, data, size);
    
    msync(mapped, size, MS_SYNC);
    
    munmap(mapped, size);
    close(fd);
    
    return 0;
}

int memory_mapped_file_read(const char *filename) {
    int fd = open(filename, O_RDONLY);
    if (fd == -1) {
        perror("open");
        return -1;
    }
    
    struct stat sb;
    if (fstat(fd, &sb) == -1) {
        perror("fstat");
        close(fd);
        return -1;
    }
    
    void *mapped = mmap(NULL, sb.st_size, PROT_READ, MAP_PRIVATE, fd, 0);
    if (mapped == MAP_FAILED) {
        perror("mmap");
        close(fd);
        return -1;
    }
    
    printf("File content:\n%.*s\n", (int)sb.st_size, (char*)mapped);
    
    munmap(mapped, sb.st_size);
    close(fd);
    
    return 0;
}
```

### 5.7.2 共享記憶體映射

```c
#include <sys/mman.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <unistd.h>
#include <stdio.h>
#include <string.h>

#define SHM_NAME "/my_shared_memory"
#define SHM_SIZE 4096

int shared_memory_example(void) {
    int shm_fd = shm_open(SHM_NAME, O_CREAT | O_RDWR, 0666);
    if (shm_fd == -1) {
        perror("shm_open");
        return -1;
    }
    
    if (ftruncate(shm_fd, SHM_SIZE) == -1) {
        perror("ftruncate");
        close(shm_fd);
        return -1;
    }
    
    void *ptr = mmap(0, SHM_SIZE, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0);
    if (ptr == MAP_FAILED) {
        perror("mmap");
        close(shm_fd);
        return -1;
    }
    
    pid_t pid = fork();
    
    if (pid == 0) {
        sprintf((char*)ptr, "Written by child at %ld", (long)time(NULL));
        printf("Child wrote to shared memory\n");
    } else {
        wait(NULL);
        printf("Parent read from shared memory: %s\n", (char*)ptr);
    }
    
    munmap(ptr, SHM_SIZE);
    close(shm_fd);
    shm_unlink(SHM_NAME);
    
    return 0;
}
```

## 5.8 非同步輸入輸出

### 5.8.1 Linux AIO

```c
#include <aio.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>

int async_io_example(void) {
    const char *filename = "async_test.txt";
    const char *data = "Async I/O test data";
    
    int fd = open(filename, O_WRONLY | O_CREAT | O_TRUNC, 0644);
    if (fd == -1) {
        perror("open");
        return -1;
    }
    
    struct aiocb cb;
    memset(&cb, 0, sizeof(struct aiocb));
    
    cb.aio_fildes = fd;
    cb.aio_buf = (void*)data;
    cb.aio_nbytes = strlen(data);
    cb.aio_offset = 0;
    
    if (aio_write(&cb) == -1) {
        perror("aio_write");
        close(fd);
        return -1;
    }
    
    while (aio_error(&cb) == EINPROGRESS) {
        printf("Writing in progress...\n");
        usleep(100000);
    }
    
    int err = aio_error(&cb);
    if (err != 0) {
        fprintf(stderr, "AIO error: %s\n", strerror(err));
        close(fd);
        return -1;
    }
    
    ssize_t ret = aio_return(&cb);
    printf("Wrote %zd bytes asynchronously\n", ret);
    
    close(fd);
    
    return 0;
}

int async_read_example(const char *filename) {
    int fd = open(filename, O_RDONLY);
    if (fd == -1) {
        perror("open");
        return -1;
    }
    
    struct stat sb;
    fstat(fd, &sb);
    
    struct aiocb cb;
    memset(&cb, 0, sizeof(struct aiocb));
    
    char *buffer = (char*)malloc(sb.st_size + 1);
    
    cb.aio_fildes = fd;
    cb.aio_buf = buffer;
    cb.aio_nbytes = sb.st_size;
    cb.aio_offset = 0;
    
    if (aio_read(&cb) == -1) {
        perror("aio_read");
        free(buffer);
        close(fd);
        return -1;
    }
    
    while (aio_error(&cb) == EINPROGRESS) {
        printf("Reading in progress...\n");
        usleep(100000);
    }
    
    buffer[sb.st_size] = '\0';
    printf("Read content: %s\n", buffer);
    
    free(buffer);
    close(fd);
    
    return 0;
}
```

## 5.9 本章小結

本章介紹了檔案系統與輸入輸出的核心概念：

1. 檔案系統的基本架構
2. inode 結構與元資料管理
3. 標準輸入輸出函式庫的使用
4. Linux 系統呼叫介面
5. 檔案鎖定機制
6. 目錄操作與遍歷
7. 緩衝區管理策略
8. 記憶體映射檔案技術
9. 非同步輸入輸出

## 5.10 習題

1. 解釋 VFS（虛擬檔案系統）在作業系統中的作用。
2. 什麼是 inode？它包含哪些資訊？
3. 比較全緩衝、行緩衝和無緩衝的差異。
4. 說明檔案鎖定的類型和實現方式。
5. 解釋 mmap 的工作原理和優點。
6. 比較同步 I/O 和非同步 I/O。
7. 實現一個遞迴目錄遍歷程式。
8. 解釋直接 I/O 和緩衝 I/O 的區別。
