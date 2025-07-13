def summarize_ranges(nums):
    """
    Summarizes a list of integers into ranges.
    For example, [0, 1, 2, 4, 5, 7] becomes ['0-2', '4-5', '7'].
    """
    if not nums:
        return []
    # convert all elements to integers
    nums = list(map(int, nums))
    nums = sorted(nums)
    result = []
    start = nums[0]
    end = nums[0]

    for n in nums[1:]:
        if n == end + 1:
            end = n
        else:
            if start == end:
                result.append(str(start))
            else:
                result.append(f"{start}-{end}")
            start = end = n

    if start == end:
        result.append(str(start))
    else:
        result.append(f"{start}-{end}")

    return result