import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt


class OptionTools:
    def calculate_yield(self):
        try:
            data_path = Path(__file__).parent.parent / "data/123.csv"
            df = pd.read_csv(data_path).sort_values('trade_date')

            # 初始化收益率列
            df['yield'] = 0.0

            for i in range(1, len(df)):
                current = df.iloc[i]
                previous = df.iloc[i - 1]

                # 计算收益率
                if current['position'] == 0:
                    # 前一天也等于0的话 代表一直空仓 pass 直接不处理默认收益是0即可
                    # 今天是0做的就是平仓操作 分情况看前一天是多头还是空头
                    # sl是多头的跌幅止损 -
                    # ul是空头的涨幅止损 +
                    # 前一天是多头的情况
                    if previous['position'] > 0:
                        # 今天是多头平仓 sl如果存在触发止损 否则按诶日结return计算收益
                        if current['sl'] < 0:
                            #盘中触发信号止损
                            df.at[i, 'yield'] = previous['position']*previous['size']*current['sl']
                        else:
                           #尾盘多头平仓
                           df.at[i, 'yield'] = previous['position']*previous['size']*current['return']
                    # 前一天是空头的情况      
                    elif previous['position'] < 0:
                        # 今天是空头平仓 ul如果存在触发止损 否则按诶日结return计算收益
                        if current['ul'] > 0:
                            #盘中触发信号止损
                            df.at[i, 'yield'] = previous['position']*previous['size']*current['ul']
                        else:
                            #尾盘空头平仓
                            df.at[i, 'yield'] = previous['position']*previous['size']*current['return']
                # 剩下两种情况 今天肯定开仓了 只有两个方向 多头 和 空头 并且开仓无止盈操作 直接仓位乘以return即可
                else:
                    # df.at[i, 'yield'] = current['position']*current['size']*current['return']
                    if current['position'] > 0:
                        if current['sl'] < 0:
                            df.at[i, 'yield'] = current['position']*current['size']*current['sl']
                        else:
                            df.at[i, 'yield'] = current['position']*current['size']*current['return']
                    elif current['position'] < 0:
                        if current['ul'] > 0:
                            df.at[i, 'yield'] = current['position']*current['size']*current['ul']
                        else:
                            df.at[i, 'yield'] = current['position']*current['size']*current['return']

            # 更新原有数据 新增yield列
            new_data_path = data_path.parent / "123_new.csv"
            # index=False 表示不保存索引列
            df.to_csv(new_data_path, index=False)

           # 初始化资产价值列，第一天的资产价值为 1
            df['asset_value'] = 0.0
            df.at[0, 'asset_value'] = 1

            # 计算每日资产价值
            for i in range(1, len(df)):
                df.at[i, 'asset_value'] = df.at[i - 1, 'asset_value'] * (1 + df.at[i, 'yield'])

            # 生成并保存图表数据
            chart_data = df[['trade_date', 'asset_value']]
            chart_data_path = data_path.parent / "chart_data_123.csv"
            chart_data.to_csv(chart_data_path, index=False)

            plt.figure(figsize=(12, 6))
            plt.plot(df['trade_date'], df['asset_value'])
            plt.title('Asset Value Trend')
            plt.xlabel('Trade Date')
            plt.ylabel('Asset Value')
            plt.xticks(rotation=45)
            plt.savefig(data_path.parent / 'yield_chart.png')
            plt.close()

            return True
        except Exception as e:
            print(f"计算收益率时发生错误: {str(e)}")
            return False

    def calculate_yield2(self):
        position = 0  # 当前持仓方向：0（空仓），1（多仓），-1（空仓）
        trade_size = 0  # 初始手数为0（未持仓）
        pnl = 0  # 累计盈亏
        entry_price = 0  # 开仓均价
        prev_signal = 0  # 初始化前一次信号

        for i in range(2, len(df_day)):
            curr = df_day.iloc[i]
            prev = df_day.iloc[i - 1]

            current_signal = curr['signal_1']  # 当前信号
            last_signal = prev['signal_1']  # 昨日信号

            # 条件1：信号一致且未平仓 → 增加手数
            if current_signal == last_signal and position != 0:
                # 检查是否触发止损止盈
                stop_loss = False
                take_profit = False

                # 多头持仓：检查止损（跌破下限）或止盈（突破上限）
                if position == 1:
                    if curr['low'] <= curr['down_lim']:
                        pnl += (curr['down_lim'] - entry_price) * trade_size
                        stop_loss = True
                    elif curr['high'] >= curr['up_lim']:
                        pnl += (curr['up_lim'] - entry_price) * trade_size
                        take_profit = True

                # 空头持仓：检查止损（突破上限）或止盈（跌破下限）
                elif position == -1:
                    if curr['high'] >= curr['up_lim']:
                        pnl += (entry_price - curr['up_lim']) * trade_size
                        stop_loss = True
                    elif curr['low'] <= curr['down_lim']:
                        pnl += (entry_price - curr['down_lim']) * trade_size
                        take_profit = True

                # 未触发止损止盈 → 加仓
                if not stop_loss and not take_profit:
                    # 计算新的开仓均价（加权平均）
                    new_entry_price = (entry_price * trade_size + curr['close']) / (trade_size + 1)
                    entry_price = new_entry_price
                    trade_size += 1

                # 触发止损止盈 → 平仓
                else:
                    position = 0
                    trade_size = 0

            # 条件2：信号不一致或首次开仓 → 平仓或开仓
            else:
                # 平仓逻辑
                if position != 0:
                    # 根据持仓方向计算盈亏
                    if position == 1:
                        pnl += (curr['close'] - entry_price) * trade_size
                    elif position == -1:
                        pnl += (entry_price - curr['close']) * trade_size
                    position = 0
                    trade_size = 0

                # 开仓逻辑（信号一致且非平仓状态）
                if current_signal == last_signal and current_signal != 0:
                    position = current_signal
                    trade_size = 1
                    entry_price = curr['close']

            prev_signal = current_signal  # 更新前信号