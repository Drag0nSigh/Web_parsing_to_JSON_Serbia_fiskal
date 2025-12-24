from typing import List


class Solution:
    def mergeSimilarItems(self, items1: List[List[int]], items2: List[List[int]]) -> List[List[int]]:
        sorted_items1 = sorted(items1, key=lambda x: x[0])
        sorted_items2 = sorted(items2, key=lambda x: x[0])
        result = []
        index_result = 0
        while len(sorted_items1) != 0 and len(sorted_items2) != 0:
            if sorted_items1[0] <= sorted_items2[0]:
                len_item2 = len(sorted_items2) - 1
                index_item2 = 0
                result.append(sorted_items1[0].copy())
                while index_item2 <= len_item2:
                    if sorted_items1[0][0] == sorted_items2[index_item2][0]:
                        result[index_result][1] += sorted_items2[index_item2][1]
                        sorted_items2.pop(index_item2)
                        len_item2 = len(sorted_items2) - 1
                        continue
                    index_item2 += 1
                sorted_items1.pop(0)

            else:
                len_item1 = len(sorted_items1) - 1
                index_item1 = 0
                result.append(sorted_items2[0])
                while index_item1 <= len_item1:
                    if sorted_items2[0][0] == sorted_items1[index_item1][0]:
                        result[index_result][1] += sorted_items1[index_item1][1]
                        sorted_items1.pop(index_item1)
                        len_item1 = len(sorted_items1) - 1
                        continue
                    index_item1 += 1
                sorted_items2.pop(0)
            index_result += 1
        (
            [result.append(i) for i in sorted_items2]
            if len(sorted_items1) == 0
            else [result.append(i) for i in sorted_items1]
        )

        return result


s = Solution()
print(s.mergeSimilarItems([[1, 1], [4, 5], [3, 8]], [[1, 1], [1, 5]]))
d = Solution()
print(d.mergeSimilarItems([[1, 1], [4, 5], [3, 8]], [[3, 1], [1, 5]]))  # [[1,6], [3,9], [4,5]]
print(d.mergeSimilarItems([[1, 1], [3, 2], [2, 3]], [[2, 1], [3, 2], [1, 3]]))
print(d.mergeSimilarItems([[1, 3], [2, 2]], [[7, 1], [2, 2], [1, 4]]))
