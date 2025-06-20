---
title: Linked List 101
---

首先我們要使用 `main.c` 來實作一個簡單的 linked list。這個 linked list 會包含以下功能：
1. 插入節點到 linked list 的尾端。
2. 列印 linked list 的內容。
3. 釋放 linked list 的記憶體。
其中，所有 linked list 的實作會位於 `list.c` 和 `list.h` 中。
我們將使用 C 語言來實作這個 linked list。這個 linked list 將會包含一個 dummy node，這樣可以簡化插入和刪除節點的操作。

先建立以下檔案：

```bash
.
├── list.c
├── list.h
└── main.c
```

## 先實作`main.c` 實作
```c
# include "list.h"

int main()
{
    Node *head = create_node(-1); // 創建一個 dummy node
    for (int i = 0; i < 5; i++)
    {
        insert_tail(head); // 插入節點到 linked list 的尾端
    }
    print_list(head); // 列印 linked list 的內容
    free_list(head); // 釋放 linked list 的記憶體
    return 0;
}
```

## 在 `list.h` 定義的結構和函式原型：

```c
typedef struct Node
{
    int data;
    struct Node *next;
} Node;

void free_list(Node *node);
void print_list(Node *node);
void insert_tail(Node *node);
```

`list.c` 實作 linked list 的函式：

```c
#include <stdio.h>
#include <stdlib.h>
#include "list.h"
void free_list(Node *node)
{
    Node *temp;
    while (node != NULL)
    {
        temp = node;
        node = node->next;
        free(temp);
    }
}
void print_list(Node *node)
{
    while (node != NULL)
    {
        printf("%d ", node->data);
        node = node->next;
    }
    printf("\n");
}
void insert_tail(Node *node)
{
    Node *new_node = malloc(sizeof(Node));
    if (new_node == NULL)
    {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    new_node->data = 0; // 預設值
    new_node->next = NULL;

    while (node->next != NULL)
    {
        node = node->next;
    }
    node->next = new_node;
}
```
## 實作 `list.c`

```c
#include <stdio.h>
#include <stdlib.h>
#include "list.h"
Node *create_node(int data)
{
    Node *new_node = malloc(sizeof(Node));
    if (new_node == NULL)
    {
        fprintf(stderr, "Memory allocation failed\n");
        exit(EXIT_FAILURE);
    }
    new_node->data = data;
    new_node->next = NULL;
    return new_node;
}
void free_list(Node *node)
{
    Node *temp;
    while (node != NULL)
    {
        temp = node;
        node = node->next;
        free(temp);
    }
}
void print_list(Node *node)
{
    while (node != NULL)
    {
        printf("%d ", node->data);
        node = node->next;
    }
    printf("\n");
}
void insert_tail(Node *node, int n)
{
    while (node->next != NULL)
    {
        node = node->next;
    }
    node->next = create_node(n);
}
```

## 編譯
```
gcc -Wall -o linked_list.out main.c list.c 
```
- `-Wall` 參數會開啟所有警告訊息，這樣可以幫助我們在編譯時發現潛在的問題。
- `-o linked_list.out` 參數指定輸出的可執行檔名稱為 `linked_list.out`。
- `gcc` 是 GNU C Compiler 的縮寫，是一個開源的 C 語言編譯器。
會產生 `linked_list.out` 可執行檔。

## 執行
```
$ ./linked_list.out 
-1 0 1 2 3 4 
```
