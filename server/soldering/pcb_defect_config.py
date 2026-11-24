PCB_DEFECT_LABELS = [
    'missing_hole',
    'mouse_bite',
    'open_circuit',
    'short',
    'spurious_copper',
    'spur',
]

PCB_DEFECT_LABEL_CN = {
    'missing_hole': '缺孔',
    'mouse_bite': '鼠咬',
    'open_circuit': '开路',
    'short': '短路',
    'spurious_copper': '杂铜',
    'spur': '毛刺',
}

PCB_DEFECT_DEDUCT = {
    'missing_hole': 15,
    'mouse_bite': 8,
    'open_circuit': 20,
    'short': 20,
    'spurious_copper': 8,
    'spur': 5,
}

PCB_DEFECT_SUGGESTIONS = {
    'missing_hole': '缺孔通常与钻孔偏移或孔位损伤有关，建议复核孔位对准并检查加工精度。',
    'mouse_bite': '鼠咬属于边缘缺损或蚀刻异常，建议检查板边加工和蚀刻质量。',
    'open_circuit': '开路会直接导致网络不导通，建议检查走线连续性和断线区域。',
    'short': '短路通常由线间距不足或连锡造成，建议检查间距并清理连桥。',
    'spurious_copper': '杂铜属于多余铜残留，建议复核蚀刻和清洗工艺。',
    'spur': '毛刺会影响电气间距和工艺质量，建议检查成型和蚀刻边界。',
}

