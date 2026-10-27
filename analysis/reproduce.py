"""Recompute saved-result statistics. Standard library; no inference or network."""
from pathlib import Path
from collections import Counter
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]

def load(path):
    return json.loads((ROOT / path).read_text())

def check(condition, message):
    if not condition:
        raise ValueError(message)


def main():
    inventory = load('RELEASE_MANIFEST.json')
    for name, sha in inventory.items():
        check(hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == sha, 'File changed: '+name)
    check({p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != 'RELEASE_MANIFEST.json'} == set(inventory), 'Inventory has extra or missing files')
    m = load('evidence/m1_cpu_result_summary.json')
    check(m['passed'] and len(m['cells']) == 18, 'M1 coverage')
    for arm, expected in [('base', [0,1,3]), ('instruct', [0,2,3])]:
        counts=[]
        for epoch in [1,2,4]:
            rows=[r for r in m['cells'] if r['arm']==arm and r['epoch']==epoch]
            check({r['seed'] for r in rows} == {1729,2718,31415}, 'M1 seeds')
            for r in rows:
                # Summary lacks structural/coverage details; this checks semantic/family agreement only.
                check(r['qualified'] == (r['minimum_class_accuracy'] >= .9 and min(r['family_success_rates'].values()) >= .9), 'M1 semantic/family gate mismatch')
            counts.append(sum(r['qualified'] for r in rows))
        check(counts == expected, 'M1 README counts')
        print('M1', arm, 'qualified seeds at epochs 1/2/4:', counts)
    a=load('reports/generated/c1_result_audit.json')
    check(a['passed'] and a['episodes_replayed']==48, 'C1 audit')
    check(all(r['episodes']==16 and r['verified_successes']==0 for r in a['models']), 'C1 outcomes')
    check(sum(r['actions'] for r in a['models']) == sum(r['valid_actions'] for r in a['models']) == 510, 'C1 actions')
    for name, predictions in [('c2_result_audit',144),('c3_result_audit',192)]:
        a=load('reports/generated/'+name+'.json')
        check(a['passed'] and a['predictions_audited']==predictions, name)
        for r in a['models']:
            changes=[c['action_changes'] for c in r['contrasts']]
            check(changes == ([0,0,0] if predictions==144 else [0,16,16,0]), name+' contrasts')
    audit=load('reports/generated/c4_result_audit.json')
    for model in audit['models']:
        seed=model['model_seed']
        report=load(f'reports/generated/c4_atomic_tool_union_execution_v1_results/base/seed-{seed}/epoch-4/evaluation_report.json')
        check(hashlib.sha256((ROOT/f'reports/generated/c4_atomic_tool_union_execution_v1_results/base/seed-{seed}/epoch-4/evaluation_report.json').read_bytes()).hexdigest()==model['report_sha256'], 'C4 original hash')
        check(report['complete'] and len(report['predictions'])==64 and report['executed_predicted_actions']==0, 'C4 completeness')
        for family, tool in [('sprint_planning','list_backlog_tickets'),('sprint_rollover','list_rollover_candidates')]:
            rows=[p for p in report['predictions'] if p['family']==family]
            pairs={}
            for p in rows:
                pair=pairs.setdefault(p['scene_position'],{})
                check(p['condition'] not in pair, 'Duplicate C4 pair')
                action=json.loads(p['action_text'])['action']
                pair[p['condition']]=action=={'type':'tool','tool':tool,'arguments':{}}
            check(len(pairs)==16 and all(set(v)=={'native4','union8'} for v in pairs.values()), 'C4 pairing')
            table=Counter({'both_correct':0,'native_correct_union_wrong':0,'native_wrong_union_correct':0,'both_wrong':0})
            for p in pairs.values():
                left,right=p['native4'],p['union8']
                table['both_correct' if left and right else 'native_correct_union_wrong' if left else 'native_wrong_union_correct' if right else 'both_wrong']+=1
            check(dict(table)==model['families'][family]['paired_correctness'], 'C4 paired correctness')
            native=sum(p['native4'] for p in pairs.values()); union=sum(p['union8'] for p in pairs.values())
            check((native,union)==((16,16) if family=='sprint_planning' else (16,0)), 'C4 README counts')
            print('C4',seed,family,'Native4 / Union8:',native,union,'of 16')
    cov=load('evidence/action_competition_coverage_audit.json')
    for split,n in [('train',20000),('development',5423)]:
        rows=[v for k,v in cov['groups'].items() if k.startswith('M1/'+split+'/')]
        check(sum(r['rows'] for r in rows)==n and all(r['both_queries_available']==0 for r in rows), 'Coverage counts')
    d=load('evidence/instruct_description_recovered_result_audit_v2.json')
    check(d['passed'] and d['logical_matrix_episodes']==96 and d['retained_verified_episodes']+d['replayed_new_episodes']==96, 'Description recovery')
    total=0
    for family,expected in [('sprint_planning',[10,10]),('sprint_rollover',[4,0]),('rollover_then_planning',[0,0])]:
        f=d['summary']['families'][family]
        check([f['conditions'][k]['successes'] for k in ['label_only','description']]==expected,'Description outcomes')
        check(sum(f['paired'].values())==16,'Description paired denominator')
        for c in f['conditions'].values():
            check(c['episodes']==16 and c['prediction_attempts']==c['structurally_valid_actions'],'Description action validity')
            total+=c['prediction_attempts']
    check(total==948,'Description saved actions')
    u=load('evidence/u1_exclusion_diagnosis_v1.json')
    check(u['sources']==18889 and u['original_components_reproduced'] and not u['membership_selected'], 'U1 scope')
    check(all(r['available']<r['required'] for r in u['original_quota_shortages']), 'U1 failed quotas')
    for p in ROOT.rglob('*.md'):
        text=p.read_text()
        check(text.count('```')%2==0,'Unbalanced code fence: '+str(p))
        for target in re.findall(r'\]\(([^)]+)\)',text):
            if '://' not in target and not target.startswith('#'):
                check((p.parent/target.split('#')[0]).exists(),'Broken link: '+target)
    print('PASS: inventory, saved-result arithmetic, C4 prediction reaggregation and relative links.')
    print('These checks do not rerun model inference or independently validate historical replay.')

if __name__=='__main__':
    main()
