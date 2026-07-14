# Binary Tree

每個節點最多有兩個子節點（left、right）的樹結構。

```c
struct TreeNode {
    int val;
    struct TreeNode *left;
    struct TreeNode *right;
};
```

## 走訪（Traversal）

- **Preorder**（前序）：root → left → right
- **Inorder**（中序）：left → root → right（BST 中序走訪得到遞增序列）
- **Postorder**（後序）：left → right → root
- **Level order**（層序）：一層一層由上而下，用 queue（BFS）實作

前三者可用遞迴或 stack（DFS）實作，時間複雜度皆為 O(n)。

## Invert binary tree（反轉樹）

把每個節點的左右子樹交換，成為鏡像樹。

```c
struct TreeNode *invert(struct TreeNode *root) {
    if (!root)
        return NULL;
    struct TreeNode *tmp = root->left;
    root->left = invert(root->right);
    root->right = invert(tmp);
    return root;
}
```

- 時間複雜度 O(n)，空間複雜度 O(h)（遞迴深度，h 為樹高）。
- 亦可用 BFS/DFS 迭代版本，逐一交換左右子節點。
