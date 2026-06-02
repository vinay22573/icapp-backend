from concurrent.futures import ThreadPoolExecutor, as_completed
import anvil.server

_executor = ThreadPoolExecutor(max_workers=8)

def call_anvil(fn_name, *args):
    return anvil.server.call(fn_name, *args)

def call_anvil_concurrent(calls):
    futures = {}
    for index, (fn_name, *args) in enumerate(calls):
        future = _executor.submit(call_anvil, fn_name, *args)
        futures[future] = index
    results = [None] * len(calls)
    for future in as_completed(futures):
        index = futures[future]
        result = future.result()
        results[index] = result
    return results