# import subprocess


# def get_agent_logs(lines: int = 100):
#     raw = subprocess.check_output(
#         ["docker", "logs", "--tail", str(lines), "quasar-agent"],
#         stderr=subprocess.STDOUT,
#     )
#     return raw.decode(errors="replace").splitlines()


# def get_collector_logs(lines: int = 100):
#     raw = subprocess.check_output(
#         ["docker", "logs", "--tail", str(lines), "quasar-collector"],
#         stderr=subprocess.STDOUT,
#     )
#     return raw.decode(errors="replace").splitlines()


# def get_retrain_log():
#     from backend.database.database import get_connection
#     with get_connection() as conn:
#         with conn.cursor() as cur:
#             cur.execute("""
#                 SELECT val_loss, real_label_count, trained_at
#                 FROM retrain_log
#                 ORDER BY trained_at DESC
#                 LIMIT 50
#             """)
#             return list(cur.fetchall())
