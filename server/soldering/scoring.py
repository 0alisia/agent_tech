CLASS_LABELS = {
    'short': '连锡短路',
    'pad_off': '焊盘脱落',
    'missing': '漏焊',
    'cold_solder': '虚焊',
    'solder_tip': '拉尖',
    'solder_uneven': '锡量不均',
}

DEDUCT_RULES = {
    'short': 20,
    'pad_off': 20,
    'missing': 10,
    'cold_solder': 10,
    'solder_tip': 5,
    'solder_uneven': 3,
}

SUGGESTIONS = {
    'short': '连锡短路通常与焊锡量过多、焊点间距控制不足有关，建议减少上锡量并用吸锡带清理桥连位置。',
    'pad_off': '焊盘脱落属于严重工艺问题，建议降低烙铁停留时间，修复前先确认焊盘与线路连接状态。',
    'missing': '漏焊会导致电路不导通，建议补焊并确认焊锡充分包覆引脚和焊盘。',
    'cold_solder': '虚焊多由温度不足或浸润不充分造成，建议重新加热焊点并补充少量焊锡形成可靠连接。',
    'solder_tip': '拉尖会影响工艺一致性，建议移开烙铁前控制焊锡表面张力，必要时重新修整焊点。',
    'solder_uneven': '锡量不均会降低焊点可靠性，建议控制送锡量并保持焊点外观饱满光亮。',
}


def grade_for_score(score):
    if score >= 90:
        return '优秀'
    if score >= 80:
        return '良好'
    if score >= 60:
        return '合格'
    return '不合格'


def score_detections(detections):
    defect_counts = {}
    total_deduct = 0
    severe_count = 0
    scored_detections = []

    for detection in detections:
        class_name = detection.get('class_name', '')
        deduct = DEDUCT_RULES.get(class_name, 0)
        label = CLASS_LABELS.get(class_name, class_name)
        if deduct:
            defect_counts[class_name] = defect_counts.get(class_name, 0) + 1
            total_deduct += deduct
            if class_name in ('short', 'pad_off'):
                severe_count += 1
        scored_detections.append({
            **detection,
            'label': label,
            'deduct': deduct,
            'scored': bool(deduct),
        })

    score = max(0, 100 - total_deduct)
    if severe_count >= 2:
        score = min(score, 59)

    parts = []
    for class_name, count in defect_counts.items():
        parts.append(f'{CLASS_LABELS.get(class_name, class_name)}{count}处')

    if parts:
        summary = f'检测到{sum(defect_counts.values())}处计分缺陷：' + '、'.join(parts) + '。'
    elif detections:
        summary = '检测到目标，但未匹配到已配置的焊点缺陷类别，当前不参与扣分。'
    else:
        summary = '未检测到焊点缺陷，建议结合人工复核确认。'

    suggestions = [SUGGESTIONS[name] for name in defect_counts if name in SUGGESTIONS]
    if not suggestions:
        suggestions = ['请保持统一光照和垂直拍摄角度，必要时由教师结合原图进行人工复核。']

    return {
        'score': score,
        'grade': grade_for_score(score),
        'total_deduct': total_deduct,
        'summary': summary,
        'suggestions': suggestions,
        'detections': scored_detections,
        'defect_counts': {
            CLASS_LABELS.get(name, name): count
            for name, count in defect_counts.items()
        },
    }

