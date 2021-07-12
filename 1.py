# 计算解数目
ans_num = dict()


def num_result(pre_ans, lst, is_chose):
    if is_chose:
        if pre_ans in ans_num.keys():
            ans_num[pre_ans] += 1
        else:
            ans_num[pre_ans] = 1
    if not lst:
        return
    num_result(pre_ans + lst[0], lst[1:], 1)
    num_result(pre_ans, lst[1:], 0)


ratio = [105, 78, 69, 67, 22, 9, 2]
num_result(0, ratio, 0)
print(ans_num)
print(max(ans_num.values()))
