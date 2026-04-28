#!/usr/bin/env python3
"""
Deterministic Reflection Agent — CLI
Loads reflection-tree.json and walks it based on user choices.
No LLM at runtime. Pure tree traversal.
"""

import json
import os
import sys
import random
import time
from datetime import datetime



RESET   = "\033[0m"
BOLD    = "\033[1m"
DIM     = "\033[2m"
ITALIC  = "\033[3m"
GOLD    = "\033[38;5;179m"
GREY    = "\033[38;5;245m"
TEAL    = "\033[38;5;109m"
PURPLE  = "\033[38;5;140m"
ROSE    = "\033[38;5;174m"
WHITE   = "\033[38;5;253m"

AXIS_COLORS = {
    "A1": TEAL,
    "A2": PURPLE,
    "A3": ROSE,
}

def clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def rule(char="─", color=DIM):
    width = min(os.get_terminal_size().columns, 72) if hasattr(os, 'get_terminal_size') else 72
    print(f"{color}{char * width}{RESET}")

def print_header():
    now = datetime.now().strftime("%H:%M")
    rule("─")
    print(f"{DIM}  END OF DAY · REFLECTION{RESET}{GREY}{'':>40}{now}{RESET}")
    rule("─")
    print()

def slow_print(text, delay=0.018, color=WHITE):
    for char in text:
        print(f"{color}{char}{RESET}", end='', flush=True)
        time.sleep(delay)
    print()

def print_node_label(label, color=GOLD):
    print(f"\n{DIM}{color}{'·' * 3} {label.upper()} {'·' * 3}{RESET}\n")

def print_question(text):
    print(f"\n{WHITE}{ITALIC}  {text}{RESET}\n")

def print_body(text):
    
    words = text.split()
    lines = []
    line = "  "
    for word in words:
        if len(line) + len(word) + 1 > 67:
            lines.append(line)
            line = "  " + word
        else:
            line += (" " if line.strip() else "") + word
    lines.append(line)
    print(f"\n{GREY}{ITALIC}")
    for l in lines:
        print(l)
    print(f"{RESET}")

def print_options(options):
    letters = ['A', 'B', 'C', 'D', 'E']
    for i, opt in enumerate(options):
        letter = letters[i] if i < len(letters) else str(i+1)
        print(f"  {DIM}{letter}{RESET}  {GREY}{opt}{RESET}")
    print()

def print_progress(visited, total):
    width = 40
    filled = int((visited / max(1, total)) * width)
    bar = f"{GOLD}{'█' * filled}{DIM}{'░' * (width - filled)}{RESET}"
    print(f"\n  {bar}  {DIM}{visited}/{total}{RESET}\n")

def print_summary_axis(label, text, color):
    rule("·", DIM)
    print(f"  {color}{DIM}{label}{RESET}")
    print(f"  {GREY}{ITALIC}{text}{RESET}")

def pause(prompt="  Press Enter to continue..."):
    print(f"\n{DIM}{prompt}{RESET}")
    input()



class AgentState:
    def __init__(self):
        self.tree = {}           
        self.current_id = None
        self.answers = {}        
        self.path = []           
        self.signals = {
            "axis1": {"internal": 0, "external": 0},
            "axis2": {"contribution": 0, "entitlement": 0},
            "axis3": {"other": 0, "self": 0},
        }
        self.total_interactive = 0
        self.interactive_visited = 0

    def record_signal(self, signal: str):
        if not signal:
            return
        parts = signal.split(":")
        if len(parts) != 2:
            return
        axis, pole = parts
        if axis in self.signals and pole in self.signals[axis]:
            self.signals[axis][pole] += 1

    def get_dominant(self, axis: str) -> str:
        s = self.signals.get(axis, {})
        if not s:
            return "mixed"
        total = sum(s.values())
        if total == 0:
            return "mixed"
        dominant = max(s, key=s.get)
        others = [v for k, v in s.items() if k != dominant]
        if others and s[dominant] == max(others):
            return "mixed"
        return dominant

    def interpolate(self, text: str) -> str:
        """Replace {nodeId.answer} placeholders with actual answers."""
        if not text:
            return ""
        import re
        def replacer(m):
            parts = m.group(1).split(".")
            if len(parts) == 2 and parts[1] == "answer":
                return self.answers.get(parts[0], m.group(0))
            return m.group(0)
        return re.sub(r'\{([^}]+)\}', replacer, text)



def load_tree(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    node_map = {}
    for node in data['nodes']:
        node_map[node['id']] = node
    return node_map

def count_interactive(tree: dict) -> int:
    return sum(1 for n in tree.values() if n['type'] == 'question')



def find_next(state: AgentState, node: dict) -> str | None:
    """Determine next node id after this one (for non-question auto-advance)."""
    if node.get('target'):
        return node['target']
   
    children = [n for n in state.tree.values()
                 if n.get('parentId') == node['id'] and n['type'] != 'decision']
    if len(children) == 1:
        return children[0]['id']
   
    dec = next((n for n in state.tree.values()
                if n.get('parentId') == node['id'] and n['type'] == 'decision'), None)
    if dec:
        return dec['id']
    return None

def resolve_decision(state: AgentState, node: dict) -> str | None:
    """Route based on parent question's answer."""
    parent_id = node.get('parentId')
    answer = state.answers.get(parent_id, '')
    for rule in (node.get('options') or []):
        if isinstance(rule, dict):
            if 'match' in rule and answer in rule['match']:
                return rule['goto']
            if 'condition' in rule:
                if eval_condition(state, rule['condition']):
                    return rule['goto']
    
    children = [n for n in state.tree.values() if n.get('parentId') == node['id']]
    if children:
        return children[0]['id']
    return None

def eval_condition(state: AgentState, cond: str) -> bool:
    """Evaluate a condition string like 'axis1.dominant=internal'."""
    try:
        axis_part, rest = cond.split('.')
        prop, val = rest.split('=')
        if prop == 'dominant':
            return state.get_dominant(axis_part) == val
    except Exception:
        pass
    return False



def render_start(state: AgentState, node: dict):
    clear()
    print_header()
    print_node_label("Welcome", GOLD)
    slow_print(f"  {state.interpolate(node['text'])}", color=WHITE)
    time.sleep(1.5)

def render_question(state: AgentState, node: dict) -> str:
    clear()
    print_header()
    print_progress(state.interactive_visited, state.total_interactive)

   
    color = GOLD
    for prefix, c in AXIS_COLORS.items():
        if node['id'].startswith(prefix):
            color = c
            break

    print_node_label("Question", color)
    print_question(state.interpolate(node['text']))
    opts = node.get('options', [])
    print_options(opts)

    letters = ['A', 'B', 'C', 'D', 'E']
    valid = {letters[i].lower(): opt for i, opt in enumerate(opts) if i < len(letters)}
  
    for opt in opts:
        valid[opt.lower()] = opt

    while True:
        raw = input(f"  {DIM}Your choice:{RESET} ").strip()
        # Check letter
        if raw.lower() in valid:
            chosen = valid[raw.lower()]
            print(f"\n  {GOLD}✓{RESET} {GREY}{chosen}{RESET}")
            time.sleep(0.4)
            return chosen
        
        if raw.isdigit() and 1 <= int(raw) <= len(opts):
            chosen = opts[int(raw) - 1]
            print(f"\n  {GOLD}✓{RESET} {GREY}{chosen}{RESET}")
            time.sleep(0.4)
            return chosen
        print(f"  {DIM}Please enter a letter (A–{letters[len(opts)-1]}) or number.{RESET}")

def render_reflection(state: AgentState, node: dict):
    clear()
    print_header()

    color = GOLD
    for prefix, c in AXIS_COLORS.items():
        if node['id'].startswith(prefix):
            color = c
            break

    print_node_label("Reflection", color)
    print_body(state.interpolate(node['text']))
    pause()

def render_bridge(state: AgentState, node: dict):
    clear()
    print_header()
    print_node_label("—", DIM)
    slow_print(f"\n  {state.interpolate(node['text'])}", delay=0.022, color=GREY)
    time.sleep(1.2)

def render_summary(state: AgentState, node: dict):
    clear()
    print_header()
    print_node_label("Today's Reflection", GOLD)

    templates = node.get('summaryTemplates', {})

   
    d1 = state.get_dominant('axis1')
    s1 = templates.get('axis1', {}).get(d1, templates.get('axis1', {}).get('mixed', ''))
    print_summary_axis("LOCUS OF CONTROL", s1, TEAL)

    
    d2 = state.get_dominant('axis2')
    s2 = templates.get('axis2', {}).get(d2, templates.get('axis2', {}).get('mixed', ''))
    print_summary_axis("CONTRIBUTION", s2, PURPLE)

   
    d3 = state.get_dominant('axis3')
    s3 = templates.get('axis3', {}).get(d3, templates.get('axis3', {}).get('expanding', ''))
    print_summary_axis("RADIUS OF CONCERN", s3, ROSE)

    rule("─")

    
    insights = templates.get('closingInsights', [])
    if insights:
        closing = insights[len(state.path) % len(insights)]
        print()
        slow_print(f"  {closing}", color=WHITE, delay=0.025)

    print()
    pause("  Press Enter to close...")

def render_end(state: AgentState, node: dict):
    clear()
    print_header()
    print_node_label("Done", DIM)
    slow_print(f"\n  {state.interpolate(node['text'])}", color=GREY, delay=0.03)
    print()
    rule("─")

    
    print(f"\n{DIM}  Session path: {' → '.join(state.path[:8])}{'...' if len(state.path) > 8 else ''}{RESET}")
    print(f"{DIM}  Signals: {json.dumps(state.signals)}{RESET}\n")



def run(tree_path: str):
    state = AgentState()

    try:
        state.tree = load_tree(tree_path)
    except FileNotFoundError:
        print(f"\nError: Could not find '{tree_path}'")
        print("Make sure reflection-tree.json is in the same folder as agent.py\n")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"\nError parsing JSON: {e}\n")
        sys.exit(1)

    state.total_interactive = count_interactive(state.tree)
    current_id = 'START'

    while current_id:
        node = state.tree.get(current_id)
        if not node:
            print(f"\nError: Node '{current_id}' not found in tree.")
            break

        state.path.append(current_id)

        
        if node.get('signal'):
            state.record_signal(node['signal'])

        ntype = node['type']

        if ntype == 'start':
            render_start(state, node)
            current_id = find_next(state, node)

        elif ntype == 'question':
            state.interactive_visited += 1
            chosen = render_question(state, node)
            state.answers[current_id] = chosen
            
            current_id = find_next(state, node)

        elif ntype == 'decision':
            current_id = resolve_decision(state, node)

        elif ntype == 'reflection':
            render_reflection(state, node)
            current_id = find_next(state, node)

        elif ntype == 'bridge':
            render_bridge(state, node)
            current_id = find_next(state, node)

        elif ntype == 'summary':
            render_summary(state, node)
            current_id = find_next(state, node)

        elif ntype == 'end':
            render_end(state, node)
            break

        else:
            
            current_id = find_next(state, node)



if __name__ == '__main__':
    tree_file = sys.argv[1] if len(sys.argv) > 1 else 'reflection-tree.json'
    run(tree_file)