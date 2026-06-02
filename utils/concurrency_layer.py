import os
import threading
import multiprocessing
from concurrent.futures import ProcessPoolExecutor

_cpu_pool = ProcessPoolExecutor(max_workers=max(1, multiprocessing.cpu_count() - 1))

def _compute_project_analytics(projects_data):
    """
    Pure CPU-bound work only.
    No Flask request objects.
    No Anvil calls.
    No DB/network calls.
    """
    total_projects = len(projects_data)
    open_projects = sum(1 for project in projects_data if project.get("open"))

    domain_distribution = {}
    sponsor_counts = {}

    for project in projects_data:
        for domain in project.get("domains", []):
            domain_distribution[domain] = domain_distribution.get(domain, 0) + 1

        sponsors = project.get("sponsors", {})
        if isinstance(sponsors, dict):
            for sponsor_id in sponsors.keys():
                sponsor_counts[sponsor_id] = sponsor_counts.get(sponsor_id, 0) + 1

    return {
        "total_projects": total_projects,
        "open_projects": open_projects,
        "closed_projects": total_projects - open_projects,
        "domain_distribution": domain_distribution,
        "per_sponsor_project_count": sponsor_counts,
        "computed_by_pid": os.getpid(),
        "computed_by_tid": threading.get_ident(),
    }

def run_project_analytics_in_process(projects_data):
    """
    Submit CPU-heavy analytics to a separate process.
    The caller can wait for result or use it in a dedicated analytics route.
    """
    future = _cpu_pool.submit(_compute_project_analytics, projects_data)
    return future