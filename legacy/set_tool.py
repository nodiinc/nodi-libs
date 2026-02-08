from typing import Any

def compare_sets_equal(set_a: set, set_b: set) -> set:
    """두 세트가 같은지 비교"""
    return set_a == set_b

def compare_sets_different(set_a: set, set_b: set) -> set:
    """두 세트가 다른지 비교"""
    return set_a != set_b

def intersection_sets(set_a: set, set_b: set) -> set:
    """두 세트의 교집합 A∩B"""
    return set_a & set_b

def union_sets(set_a: set, set_b: set) -> set:
    """두 세트의 합집합 A∪B"""
    return set_a | set_b

def difference_sets(set_a: set, set_b: set) -> set:
    """두 세트의 차집합 A-B"""
    return set_a - set_b

def difference_sets_symmetric(set_a: set, set_b: set) -> set:
    """두 세트의 대칭차집합 A△B = (A-B)∪(B-A) = (A∪B)-(A∩B)"""
    return set_a ^ set_b

def add_to_set(set_a: set, value: Any) -> set:
    """세트에 개별 값 추가"""
    set_a.add(value)
    return set_a

def update_to_set(set_a: set, set_b: set) -> set:
    """세트에 다른 세트 추가"""
    set_a.update(set_b)
    return set_a

def remove_set(set_a: set, value: Any) -> set:
    """세트에서 개별 값 제거"""
    set_a.remove(value)
    return set_a


if __name__ == '__main__':
    set_a = {1,1,2,3,4,5,6}
    set_b = {3,4,5,6,7,7,8,9}
    print(update_to_set(set_a, set_b))
