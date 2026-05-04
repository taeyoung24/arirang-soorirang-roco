def str_similarity(str1: str, str2: str, allow_blank=False) -> float:
    '''
    두 문자열의 유사도를 레벤슈타인 거리 알고리즘을 사용하여 0~1 사이의 값으로 계산하는 함수
    '''
    # 대소문자 구분 없애기
    str1 = str1.lower()
    str2 = str2.lower()

    if not allow_blank:
        str1 = str1.replace(' ', '')
        str2 = str2.replace(' ', '')


    if not str1 and not str2: return 1.0
    elif not str1 or not str2: return 0.0
    
    # 레벤슈타인 거리 계산을 위한 매트릭스 초기화
    len1, len2 = len(str1), len(str2)
    matrix = [[0] * (len2 + 1) for _ in range(len1 + 1)]
    
    # 첫 번째 행과 열 초기화
    for i in range(len1 + 1):
        matrix[i][0] = i
    for j in range(len2 + 1):
        matrix[0][j] = j
    
    # 레벤슈타인 거리 계산
    for i in range(1, len1 + 1):
        for j in range(1, len2 + 1):
            if str1[i-1] == str2[j-1]:
                matrix[i][j] = matrix[i-1][j-1]
            else:
                matrix[i][j] = min(matrix[i-1][j], matrix[i][j-1], matrix[i-1][j-1]) + 1
    
    # 레벤슈타인 거리를 유사도로 변환 (0~1 사이의 값)
    max_len = max(len1, len2)
    similarity = 1 - (matrix[len1][len2] / max_len)
    
    return similarity