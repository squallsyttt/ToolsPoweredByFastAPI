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
