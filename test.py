def calculate_charging_cost(start_minutes, end_minutes, power_mode):
    # # ʱ��ת��Ϊ����
    # start_hour, start_minute = map(int, start_time.split(':'))
    # end_hour, end_minute = map(int, end_time.split(':'))
    # start_minutes = start_hour * 60 + start_minute
    # end_minutes = end_hour * 60 + end_minute
    if end_minutes < start_minutes:
        total_cost = calculate_charging_cost(start_minutes, 1440, power_mode) + calculate_charging_cost(0, end_minutes,
                                                                                                        power_mode)
        return total_cost
    else:
        # ������ʱ�䣨���ӣ�
        total_minutes = end_minutes - start_minutes

        # ���ݳ�繦��ģʽȷ����繦��
        if power_mode == 'F':
            charging_power = 30
        elif power_mode == 'T':
            charging_power = 7
        else:
            return "Invalid charging power mode."

        # �����ʱ��ƽʱ����ʱʱ��Σ����ӣ�
        peak1_start = 10 * 60
        peak1_end = 15 * 60
        peak2_start = 18 * 60
        peak2_end = 21 * 60
        off_peak1_start = 7 * 60
        off_peak1_end = 10 * 60
        off_peak2_start = 15 * 60
        off_peak2_end = 18 * 60
        off_peak3_start = 21 * 60
        off_peak3_end = 23 * 60
        valley1_start = 23 * 60
        valley1_end = 24 * 60
        valley2_start = 0 * 60
        valley2_end = 7 * 60

        # # ��ʱ��ƽʱ����ʱ��ʱ�䣨���ӣ�
        # peak1_time = 0
        # peak2_time = 0
        # off_peak1_time = 0
        # off_peak2_time = 0
        # off_peak3_time = 0
        # valley1_time = 0
        # valley2_time = 0
        #
        # # ��ʱ��ƽʱ����ʱ��ʱ�䣨Сʱ
        # peak_hours = 0
        # off_peak_hours = 0
        # valley_hours = 0

        # �����ʱ��ƽʱ����ʱ��ʱ�䣨���ӣ�
        peak1_time = max(0, min(end_minutes, peak1_end) - max(start_minutes, peak1_start))
        peak2_time = max(0, min(end_minutes, peak2_end) - max(start_minutes, peak2_start))
        off_peak1_time = max(0, min(end_minutes, off_peak1_end) - max(start_minutes, off_peak1_start))
        off_peak2_time = max(0, min(end_minutes, off_peak2_end) - max(start_minutes, off_peak2_start))
        off_peak3_time = max(0, min(end_minutes, off_peak3_end) - max(start_minutes, off_peak3_start))
        valley1_time = max(0, min(end_minutes, valley1_end) - max(start_minutes, valley1_start))
        valley2_time = max(0, min(end_minutes, valley2_end) - max(start_minutes, valley2_start))

        # ת��ΪСʱ
        peak_hours = (peak1_time + peak2_time) / 60
        off_peak_hours = (off_peak1_time + off_peak2_time + off_peak3_time) / 60
        valley_hours = (valley1_time + valley2_time) / 60

        # ���������
        charging_kWh = charging_power * total_minutes / 60

        # ���������
        peak_price = 1.0  # ��ʱ��ۣ�Ԫ/�ȣ�
        off_peak_price = 0.7  # ƽʱ��ۣ�Ԫ/�ȣ�
        valley_price = 0.4  # ��ʱ��ۣ�Ԫ/�ȣ�
        serv_price = 0.8  # ����ѵ��ۣ�Ԫ/�ȣ�

        charging_cost = peak_hours * peak_price * charging_power + off_peak_hours * off_peak_price * charging_power + valley_hours * valley_price * charging_power

        # ����������
        service_cost = serv_price * charging_kWh

        # �����ܷ���
        total_cost = charging_cost + service_cost

        # print(peak_hours, off_peak_hours, valley_hours, charging_kWh, charging_cost, service_cost)
        return charging_cost, service_cost, total_cost

charge, server, total = calculate_charging_cost(380, 390,'F')
print(charge)
print(server)
print(total)