import json
import sys
from pathlib import Path
from collections import defaultdict

def calculate_prompt_average_times(json_file_path):
    """
    计算每个prompt分组的平均耗时，然后计算所有分组的总体平均值
    
    参数:
        json_file_path: JSON文件路径
    """
    try:
        # 读取JSON文件
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查数据结构
        if not isinstance(data, list) or len(data) == 0:
            print("错误: JSON文件格式不正确，应该是非空列表")
            return
        
        # 第一个元素包含所有details
        first_item = data[0]
        details = first_item.get("details", [])
        
        if not details:
            print("错误: 没有找到details数据")
            return
        
        print(f"分析报告: {json_file_path}")
        print(f"提示词基准: {first_item.get('basement', '未知')}")
        print(f"总次数: {first_item.get('total', 0)}")
        print(f"成功次数: {first_item.get('success', 0)}")
        print(f"失败次数: {first_item.get('failed', 0)}")
        print(f"详细条目数: {len(details)}")
        print("=" * 60)
        
        # 按照text字段对成功条目进行分组
        prompt_groups = defaultdict(list)
        
        # 遍历details进行分组
        for detail in details:
            if detail.get("status") == "success":
                text = detail.get("text", "")
                if text:  # 确保text不为空
                    prompt_groups[text].append(detail)
        
        print(f"找到 {len(prompt_groups)} 个不同的prompt分组")
        print("-" * 60)
        
        # 存储每个分组的统计结果
        group_stats = []
        
        # 计算每个分组的平均值
        for idx, (text, group_items) in enumerate(prompt_groups.items(), 1):
            group_size = len(group_items)
            
            # 初始化统计变量
            total_rewrite_seconds = 0.0
            total_motion_seconds = 0.0
            total_all_seconds = 0.0
            
            # 获取duration值（所有条目应该相同）
            duration_value = group_items[0].get("duration", 0.0)
            
            # 验证所有条目的duration是否一致
            durations = [item.get("duration", 0.0) for item in group_items]
            if len(set(durations)) > 1:
                print(f"警告: 分组 {idx} 中的duration值不一致: {durations}")
            
            # 计算总和
            for item in group_items:
                rewrite_time = item.get("rewrite_elapsed_seconds", 0)
                motion_time = item.get("motion_elapsed_seconds", 0)
                total_time = item.get("total_elapsed_seconds", 0)
                
                total_rewrite_seconds += rewrite_time
                total_motion_seconds += motion_time
                total_all_seconds += total_time
            
            # 计算分组平均值
            avg_rewrite = total_rewrite_seconds / group_size
            avg_motion = total_motion_seconds / group_size
            avg_total = total_all_seconds / group_size
            
            # 存储分组统计结果
            group_stats.append({
                "text": text,
                "duration": duration_value,
                "count": group_size,
                "avg_rewrite": avg_rewrite,
                "avg_motion": avg_motion,
                "avg_total": avg_total
            })
            
            # 输出分组信息
            print(f"分组 {idx}:")
            print(f"  Prompt文本: {text[:50]}{'...' if len(text) > 50 else ''}")
            print(f"  Duration: {duration_value} 秒")
            print(f"  重复次数: {group_size}")
            print(f"  文本重写平均耗时: {avg_rewrite:.2f} 秒")
            print(f"  动作生成平均耗时: {avg_motion:.2f} 秒")
            print(f"  总处理平均耗时: {avg_total:.2f} 秒")
            print(f"  每个seed平均生成时间: {avg_motion/4:.2f} 秒")
            print("-" * 40)
        
        print("=" * 60)
        print("分组统计汇总:")
        print("=" * 60)
        
        # 计算所有分组的总体平均值
        if group_stats:
            total_groups = len(group_stats)
            total_avg_rewrite = sum(stat["avg_rewrite"] for stat in group_stats) / total_groups
            total_avg_motion = sum(stat["avg_motion"] for stat in group_stats) / total_groups
            total_avg_total = sum(stat["avg_total"] for stat in group_stats) / total_groups
            
            # 输出总体统计
            print(f"分组总数: {total_groups}")
            print(f"总体文本重写平均耗时: {total_avg_rewrite:.2f} 秒")
            print(f"总体动作生成平均耗时: {total_avg_motion:.2f} 秒")
            print(f"总体总处理平均耗时: {total_avg_total:.2f} 秒")
            print(f"总体总处理平均耗时(分钟): {total_avg_total/60:.2f} 分钟")
            
            # 额外统计信息
            print("\n额外统计信息:")
            print(f"  总体平均每个seed生成时间: {total_avg_motion/4:.2f} 秒")
            print(f"  总体重写阶段占比: {total_avg_rewrite/total_avg_total*100:.1f}%")
            print(f"  总体动作生成占比: {total_avg_motion/total_avg_total*100:.1f}%")
            
            # 输出每个分组的详细统计表格
            print("\n详细分组统计:")
            print("-" * 100)
            print(f"{'序号':<4} {'重复次数':<8} {'Duration':<10} {'重写平均(s)':<12} {'生成平均(s)':<12} {'总平均(s)':<12} {'Prompt(前30字符)'}")
            print("-" * 100)
            for idx, stat in enumerate(group_stats, 1):
                print(f"{idx:<4} {stat['count']:<8} {stat['duration']:<10.1f} "
                      f"{stat['avg_rewrite']:<12.2f} {stat['avg_motion']:<12.2f} "
                      f"{stat['avg_total']:<12.2f} {stat['text'][:30]}{'...' if len(stat['text']) > 30 else ''}")
            
            # 导出详细统计到文件
            export_detailed_stats(group_stats, json_file_path, total_avg_rewrite, total_avg_motion, total_avg_total)
            
        else:
            print("错误: 没有找到可统计的分组")
            
    except FileNotFoundError:
        print(f"错误: 找不到文件 {json_file_path}")
    except json.JSONDecodeError as e:
        print(f"错误: JSON文件解析失败 - {e}")
    except Exception as e:
        print(f"错误: {e}")

def export_detailed_stats(group_stats, json_file_path, total_avg_rewrite, total_avg_motion, total_avg_total):
    """导出详细统计结果到文件"""
    try:
        # 创建导出文件名
        json_path = Path(json_file_path)
        export_file = json_path.parent / f"{json_path.stem}_analysis.json"
        
        # 准备导出数据
        export_data = {
            "summary": {
                "total_groups": len(group_stats),
                "total_avg_rewrite_seconds": total_avg_rewrite,
                "total_avg_motion_seconds": total_avg_motion,
                "total_avg_total_seconds": total_avg_total,
                "total_avg_per_seed_seconds": total_avg_motion / 4,
                "rewrite_percentage": total_avg_rewrite / total_avg_total * 100 if total_avg_total > 0 else 0,
                "motion_percentage": total_avg_motion / total_avg_total * 100 if total_avg_total > 0 else 0
            },
            "group_details": group_stats
        }
        
        # 导出到JSON文件
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n详细统计结果已导出到: {export_file}")
        
        # 同时导出简化的CSV格式
        csv_file = json_path.parent / f"{json_path.stem}_analysis.csv"
        with open(csv_file, 'w', encoding='utf-8') as f:
            # 写入标题
            f.write("序号,重复次数,Duration,重写平均(s),生成平均(s),总平均(s),Prompt\n")
            # 写入数据
            for idx, stat in enumerate(group_stats, 1):
                # 处理CSV中的逗号和引号
                prompt_text = stat['text'].replace('"', '""')
                if ',' in prompt_text or '"' in prompt_text:
                    prompt_text = f'"{prompt_text}"'
                
                f.write(f'{idx},{stat["count"]},{stat["duration"]:.1f},'
                       f'{stat["avg_rewrite"]:.2f},{stat["avg_motion"]:.2f},'
                       f'{stat["avg_total"]:.2f},{prompt_text}\n')
        
        print(f"CSV格式结果已导出到: {csv_file}")
        
    except Exception as e:
        print(f"警告: 导出统计结果失败 - {e}")

def main():
    # 使用方法
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        # 如果没有提供命令行参数，尝试使用默认文件名
        default_files = [
            "report.json",
            "output_report.json",
            "processing_report.json",
            "./output/local_infer/report.json"
        ]
        
        json_file = None
        for file in default_files:
            if Path(file).exists():
                json_file = file
                break
        
        if not json_file:
            print("请提供JSON文件路径作为参数")
            print("用法: python calculate_prompt_times.py <json_file_path>")
            print("\n或者将脚本放在包含report.json的目录中运行")
            return
    
    calculate_prompt_average_times(json_file)

if __name__ == "__main__":
    main()
