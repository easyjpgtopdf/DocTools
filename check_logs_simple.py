import subprocess
import sys

cmd = [
    'gcloud', 'logging', 'read',
    'resource.type=cloud_run_revision AND resource.labels.service_name=pdf-to-excel-backend AND textPayload=~"LAYOUT EMPTY STATUS"',
    '--limit', '1',
    '--format=value(textPayload)',
    '--project', 'easyjpgtopdf-de346'
]

result = subprocess.run(cmd, capture_output=True, text=True)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr, file=sys.stderr)

