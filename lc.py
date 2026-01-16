from typing import List


class Solution:
    def maximizeSquareHoleArea(
        self, n: int, m: int, hBars: List[int], vBars: List[int]
    ) -> int:
        hBars.sort()
        vBars.sort()

        x, xm, prev = 0, 0, 1

        for i in hBars:
            if i not in [1, n + 2]:
                if i - prev == 1:
                    x += 1
                else:
                    x = 1
            xm = max(xm, x)
            prev = i

        y, ym, prev = 0, 0, 1

        for i in vBars:
            if i not in [1, m + 2]:
                if i - prev == 1:
                    y += 1
                else:
                    y = 1
            ym = max(ym, y)
            prev = i

        return (min(xm, ym) + 1) ** 2


print(Solution().maximizeSquareHoleArea(2, 1, [2, 3], [2]))
print(Solution().maximizeSquareHoleArea(1, 1, [2], [2]))
print(Solution().maximizeSquareHoleArea(2, 3, [2, 3], [2, 4]))
