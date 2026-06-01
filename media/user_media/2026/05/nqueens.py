def is_safe(board, row, col, n):
    # التحقق من العمود
    for i in range(row):
        if board[i][col] == 1:
            return False
    # التحقق من القطر الأيسر العلوي
    for i, j in zip(range(row, -1, -1), range(col, -1, -1)):
        if board[i][j] == 1:
            return False
    # التحقق من القطر الأيمن العلوي
    for i, j in zip(range(row, -1, -1), range(col, n)):
        if board[i][j] == 1:
            return False
    return True

def solve_nqueens(board, row, n):
    if row == n:
        # طباعة الحل
        for r in board:
            print(r)
        print("------")
        return True
    success = False
    for col in range(n):
        if is_safe(board, row, col, n):
            board[row][col] = 1
            success = solve_nqueens(board, row + 1, n) or success
            board[row][col] = 0  # التراجع
    return success

# تشغيل الخوارزمية
n = 4  # يمكن تغييرها إلى 8 أو أي رقم
board = [[0] * n for _ in range(n)]
print(f"حلول مشكلة {n} وزيرات:")
solve_nqueens(board, 0, n)