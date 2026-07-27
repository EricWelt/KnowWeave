"""生成演示笔记数据（合成内容，用于测试 RAG 与 Agent）。

用法: python scripts/seed_demo_notes.py [--user USERNAME] [--count N]
需要先有用户（或注册接口创建）。
"""
import argparse
import asyncio
import os
import sys

# 把仓库根目录加入 sys.path（脚本以包方式导入 backend.*）
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

DEMO_NOTES = [
    ("操作系统-进程调度",
     "# 进程调度\n\n进程调度决定哪个就绪进程获得 CPU。\n\n## 常见算法\n- 先来先服务 FCFS\n- 短作业优先 SJF\n- 时间片轮转 RR\n- 优先级调度\n\n## 关键概念\n周转时间 = 完成时间 - 到达时间。\n银行家算法用于死锁避免。"),
    ("操作系统-内存管理",
     "# 内存管理\n\n虚拟内存允许程序使用比物理内存更大的地址空间。\n\n## 分页\n页表将虚拟地址映射到物理地址。\n\n## 页面置换\n- FIFO\n- LRU\n- 时钟算法\n\n缺页中断时选择被置换的页。"),
    ("计算机网络-传输层",
     "# 传输层\n\nTCP 提供可靠、面向连接的字节流服务。\n\n## TCP 三次握手\nSYN → SYN+ACK → ACK。\n\n## 拥塞控制\n慢启动、拥塞避免、快重传、快恢复。"),
    ("数据结构-排序算法",
     "# 排序算法\n\n## 比较排序\n- 快速排序: 平均 O(n log n)\n- 归并排序: 稳定 O(n log n)\n- 堆排序: O(n log n)\n\n## 非比较排序\n- 计数排序\n- 基数排序\n\n快排是工程中最常用的排序。"),
    ("数据库-事务与隔离",
     "# 事务\n\nACID: 原子性、一致性、隔离性、持久性。\n\n## 隔离级别\n- 读未提交\n- 读已提交\n- 可重复读\n- 串行化\n\n脏读、不可重复读、幻读对应不同隔离级别。"),
]


async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--username", default="demo", help="目标用户名（不存在则创建）")
    parser.add_argument("--count", type=int, default=5)
    args = parser.parse_args()

    os.chdir(os.path.join(os.path.dirname(__file__), ".."))
    from backend.database import async_session, init_db
    from backend.models import Note, User
    from backend.core.security import hash_password
    from backend.rag.indexer import index_note

    await init_db()
    async with async_session() as session:
        # 确保用户存在
        from sqlalchemy import select
        user = await session.scalar(select(User).where(User.username == args.username))
        if user is None:
            user = User(username=args.username, password_hash=hash_password("demo123456"))
            session.add(user)
            await session.commit()
            await session.refresh(user)
            print(f"已创建用户 {args.username} (密码 demo123456)")

        created = 0
        for title, content in DEMO_NOTES[: args.count]:
            note = Note(user_id=user.id, title=title, content=content, source_type="manual")
            session.add(note)
            await session.commit()
            await session.refresh(note)
            await index_note(note, session)
            created += 1
            print(f"已入库: {title}")
        print(f"完成：共 {created} 篇笔记（已向量化）")


if __name__ == "__main__":
    asyncio.run(main())
