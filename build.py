#!/usr/bin/env python3

from __future__ import annotations
import datetime
import hashlib
import os
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, List, Optional, Tuple, Union

from dateutil import relativedelta
from lxml import etree
import requests

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent

BIRTH_DATE = datetime.datetime(2004, 7, 23)

SYSTEM_INFO: List[Dict[str, str]] = [
    {"label": "OS", "value": "Windows 11, Ubuntu Linux"},
    {"label": "Role", "value": "Backend-focused Full-Stack Engineer"},
    {"label": "Location", "value": "Dhaka, Bangladesh"},
    {"label": "Education", "value": "B.Sc. in CSE, East West University"},
    {"label": "IDE & Tools", "value": "VS Code, Git, Docker"},
    {"label": "Languages", "value": "English, Bengali"},
]

CORE_PROFICIENCY: List[Dict[str, Union[str, int]]] = [
    {"name": "Backend Architecture", "level": 90},
    {"name": "Node.js / TypeScript", "level": 90},
    {"name": "SQL & Query Tuning", "level": 85},
    {"name": "DevOps & AWS CI/CD", "level": 85},
    {"name": "Next.js & Frontend", "level": 80},
    {"name": "Distributed Systems", "level": 80},
    {"name": "Testing & QA (Vitest)", "level": 85},
    {"name": "NoSQL & Caching", "level": 75},
]

CONNECT_INFO: List[Dict[str, str]] = [
    {"label": "Email", "value": "adib23704@gmail.com"},
    {"label": "LinkedIn", "value": "in/adib23704"},
    {"label": "Portfolio", "value": "adibdev.me"},
]

TECH_STACK: List[Dict[str, str]] = [
    {"label": "Languages", "value": "TypeScript, JavaScript, Python, SQL"},
    {"label": "Backend", "value": "Node.js, Express, Fastify, NestJS"},
    {"label": "APIs", "value": "RESTful, WebSockets, GraphQL, tRPC"},
    {"label": "Databases", "value": "PostgreSQL, MySQL, Redis, MongoDB"},
    {"label": "Cloud & DevOps", "value": "AWS (EC2, S3, CloudFront), Docker"},
    {"label": "CI/CD & Infra", "value": "GitHub Actions, Nginx, Linux"},
    {"label": "Frontend", "value": "Next.js, React, Tailwind CSS, Redux"},
]

FEATURED_REPOSITORIES: List[Union[str, Dict[str, str]]] = [
    "https://github.com/Adib23704/Tuya-Smart-Taskbar",
    "https://github.com/Adib23704/MoodTunes",
    "https://github.com/Adib23704/MetaPeek",
    "https://github.com/Adib23704/FlowTrack",
]

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "").strip()
HEADERS = {"authorization": f"token {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}
USER_NAME = (os.environ.get("USER_NAME") or "Adib23704").strip() or "Adib23704"

QUERY_COUNT: Dict[str, int] = {
    "user_getter": 0,
    "follower_getter": 0,
    "graph_repos_stars": 0,
    "recursive_loc": 0,
    "graph_commits": 0,
    "loc_query": 0,
    "highlights_getter": 0,
}

TRANSIENT_STATUS = (429, 500, 502, 503, 504)


def query_count(funct_id: str) -> None:
    if funct_id in QUERY_COUNT:
        QUERY_COUNT[funct_id] += 1


def post_graphql(
    query: str, variables: Dict[str, Any], retries: int = 4
) -> Optional[requests.Response]:
    if not ACCESS_TOKEN:
        return None

    delay = 2
    for attempt in range(retries):
        try:
            res = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=HEADERS,
                timeout=30,
            )
            if res.status_code not in TRANSIENT_STATUS:
                return res
            retry_after = res.headers.get("Retry-After")
            wait_time = (
                int(retry_after) if retry_after and retry_after.isdigit() else delay
            )
            print(
                f"   [GraphQL] Transient status {res.status_code}, retrying in {wait_time}s ({attempt + 1}/{retries})..."
            )
            time.sleep(wait_time)
            delay *= 2
        except requests.exceptions.RequestException as e:
            if attempt == retries - 1:
                print(f"   [GraphQL] Request failed: {e}")
                return None
            time.sleep(delay)
            delay *= 2
    return None


def simple_request(
    func_name: str, query: str, variables: Dict[str, Any]
) -> Optional[requests.Response]:
    res = post_graphql(query, variables)
    if res is not None and res.status_code == 200:
        return res
    status = res.status_code if res is not None else "No Token / Error"
    return res


def find_and_replace(root: etree._Element, element_id: str, new_text: str) -> None:
    element = root.find(f".//*[@id='{element_id}']")
    if element is not None:
        element.text = str(new_text)


def format_field_row(
    root: etree._Element,
    label: str,
    value: str,
    label_id: str,
    dots_id: str,
    val_id: str,
    total_width: int,
) -> None:
    prefix = f". {label}"
    val_str = str(value)
    gap = total_width - len(prefix) - len(val_str)
    dots = " " * max(0, gap) if gap <= 2 else " " + ("." * (gap - 2)) + " "

    find_and_replace(root, label_id, label)
    find_and_replace(root, dots_id, dots)
    find_and_replace(root, val_id, val_str)


def format_dots_value(
    root: etree._Element, label: str, element_id: str, value: Any, total_width: int = 57
) -> None:
    val_str = f"{value:,}" if isinstance(value, int) else str(value)
    gap = total_width - len(label) - len(val_str)
    dots = " " * max(0, gap) if gap <= 2 else " " + ("." * (gap - 2)) + " "

    find_and_replace(root, f"{element_id}_dots", dots)
    find_and_replace(root, element_id, val_str)


def render_proficiency_item(
    item: Dict[str, Any],
    total_width: int = 56,
    bar_len: int = 16,
    bar_start_col: int = 32,
) -> Dict[str, str]:
    name = str(item.get("name", ""))
    level = int(item.get("level", 0))

    filled_count = int(round((level / 100.0) * bar_len))
    filled_count = max(0, min(bar_len, filled_count))
    empty_count = bar_len - filled_count

    fill_str = "█" * filled_count
    empty_str = "░" * empty_count
    val_str = f"{level}%"

    prefix = f". {name}"
    gap = bar_start_col - len(prefix)
    dots = " " * max(0, gap) if gap <= 2 else " " + ("." * (gap - 2)) + " "

    return {
        "name": name,
        "dots": dots,
        "fill": fill_str,
        "empty": empty_str,
        "val": val_str,
    }


def parse_repo_link(link: Union[str, Dict[str, str]]) -> Tuple[str, str]:
    if isinstance(link, dict):
        link = link.get("url", "")
    match = re.search(r"github\.com/([^/]+)/([^/]+)", str(link))
    if match:
        return match.group(1), match.group(2).rstrip(".git")
    parts = str(link).strip("/").split("/")
    if len(parts) == 2:
        return parts[0], parts[1]
    return USER_NAME, str(link)


def get_languages_for_repo(owner: str, repo_name: str) -> List[str]:
    query = """
    query ($owner: String!, $name: String!) {
        repository(owner: $owner, name: $name) {
            languages(first: 6, orderBy: {field: SIZE, direction: DESC}) {
                nodes {
                    name
                }
            }
        }
    }"""
    try:
        req = post_graphql(query, {"owner": owner, "name": repo_name})
        if req is not None and req.status_code == 200:
            nodes = (
                req.json()
                .get("data", {})
                .get("repository", {})
                .get("languages", {})
                .get("nodes", [])
            )
            if nodes:
                return [n["name"] for n in nodes if n and "name" in n]
    except Exception:
        pass

    try:
        url = f"https://api.github.com/repos/{owner}/{repo_name}/languages"
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return list(res.json().keys())
    except Exception:
        pass
    return ["Dev"]


def format_languages(langs: List[str], max_len: int = 28) -> str:
    if not langs:
        return "Dev"
    for count in range(len(langs), 0, -1):
        candidate = ", ".join(langs[:count])
        if len(candidate) <= max_len:
            return candidate
    return str(langs[0])[:max_len]


def highlights_getter(
    repo_links: List[Union[str, Dict[str, str]]],
) -> List[Dict[str, Any]]:
    results = []
    for item in repo_links[:4]:
        custom_lang = item.get("lang") if isinstance(item, dict) else None
        custom_title = item.get("title") if isinstance(item, dict) else None

        owner, repo_name = parse_repo_link(item)
        if not repo_name:
            continue

        query_count("highlights_getter")

        if custom_lang:
            langs = [l.strip() for l in custom_lang.split(",")]
        else:
            langs = get_languages_for_repo(owner, repo_name)
            if not langs:
                langs = ["Dev"]

        name = custom_title or repo_name
        results.append({"name": name, "langs": langs})
    return results


def daily_readme(birthday: datetime.datetime) -> str:
    diff = relativedelta.relativedelta(datetime.datetime.today(), birthday)
    plural = lambda n: "s" if n != 1 else ""
    bday_emoji = " 🎂" if (diff.months == 0 and diff.days == 0) else ""
    return f"{diff.years} year{plural(diff.years)}, {diff.months} month{plural(diff.months)}, {diff.days} day{plural(diff.days)}{bday_emoji}"


def user_getter(username: str) -> Tuple[Dict[str, str], str]:
    query_count("user_getter")
    query = """
    query($login: String!) {
        user(login: $login) {
            id
            createdAt
        }
    }"""
    req = simple_request(user_getter.__name__, query, {"login": username})
    if req and req.status_code == 200:
        data = req.json().get("data", {}).get("user", {})
        return {"id": data.get("id", "")}, data.get("createdAt", "2019-02-20T19:16:01Z")

    try:
        res = requests.get(
            f"https://api.github.com/users/{username}", headers=HEADERS, timeout=10
        )
        if res.status_code == 200:
            data = res.json()
            return {"id": data.get("node_id", "")}, data.get(
                "created_at", "2019-02-20T19:16:01Z"
            )
    except Exception:
        pass
    return {"id": ""}, "2019-02-20T19:16:01Z"


def follower_getter(username: str) -> int:
    query_count("follower_getter")
    query = """
    query($login: String!) {
        user(login: $login) {
            followers {
                totalCount
            }
        }
    }"""
    try:
        req = simple_request(follower_getter.__name__, query, {"login": username})
        if req and req.status_code == 200:
            count = (
                req.json()
                .get("data", {})
                .get("user", {})
                .get("followers", {})
                .get("totalCount")
            )
            if count is not None:
                return int(count)
    except Exception:
        pass

    try:
        res = requests.get(
            f"https://api.github.com/users/{username}", headers=HEADERS, timeout=10
        )
        if res.status_code == 200:
            return int(res.json().get("followers", 25))
    except Exception:
        pass
    return 25


def graph_repos_stars(
    count_type: str, owner_affiliation: List[str], cursor: Optional[str] = None
) -> int:
    query_count("graph_repos_stars")
    query = """
    query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 100, after: $cursor, ownerAffiliations: $owner_affiliation) {
                totalCount
                edges {
                    node {
                        stargazers {
                            totalCount
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }"""
    try:
        req = simple_request(
            graph_repos_stars.__name__,
            query,
            {
                "owner_affiliation": owner_affiliation,
                "login": USER_NAME,
                "cursor": cursor,
            },
        )
        if req and req.status_code == 200:
            repos_data = (
                req.json().get("data", {}).get("user", {}).get("repositories", {})
            )
            if count_type == "repos":
                return int(repos_data.get("totalCount", 0))
            elif count_type == "stars":
                total_stars = 0
                for edge in repos_data.get("edges", []):
                    if edge.get("node") and "stargazers" in edge["node"]:
                        total_stars += edge["node"]["stargazers"].get("totalCount", 0)
                return total_stars
    except Exception:
        pass

    try:
        res = requests.get(
            f"https://api.github.com/users/{USER_NAME}/repos?per_page=100&type=all",
            headers=HEADERS,
            timeout=10,
        )
        if res.status_code == 200:
            repos = res.json()
            if count_type == "repos":
                return len(repos)
            elif count_type == "stars":
                return sum(
                    r.get("stargazers_count", 0) for r in repos if isinstance(r, dict)
                )
    except Exception:
        pass
    return 104 if count_type == "repos" else 22


def commit_counter(comment_size: int = 7) -> int:
    cache_path = (
        BASE_DIR
        / "cache"
        / f"{hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest()}.txt"
    )
    if not cache_path.is_file():
        return 2860

    total = 0
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[comment_size:]
        for line in lines:
            parts = line.split()
            if len(parts) >= 3 and parts[2].isdigit():
                total += int(parts[2])
    except Exception:
        return 2860
    return total if total > 0 else 2860


def recursive_loc(
    owner: str,
    repo_name: str,
    cursor: Optional[str] = None,
    owner_id: Optional[str] = None,
) -> Tuple[int, int, int]:
    query_count("recursive_loc")
    query = """
    query ($repo_name: String!, $owner: String!, $cursor: String) {
        repository(name: $repo_name, owner: $owner) {
            defaultBranchRef {
                target {
                    ... on Commit {
                        history(first: 100, after: $cursor) {
                            totalCount
                            edges {
                                node {
                                    author {
                                        user {
                                            id
                                        }
                                    }
                                    deletions
                                    additions
                                }
                            }
                            pageInfo {
                                endCursor
                                hasNextPage
                            }
                        }
                    }
                }
            }
        }
    }"""
    additions = 0
    deletions = 0
    my_commits = 0
    curr_cursor = cursor

    while True:
        req = post_graphql(
            query, {"repo_name": repo_name, "owner": owner, "cursor": curr_cursor}
        )
        if not req or req.status_code != 200:
            break
        repo_data = req.json().get("data", {}).get("repository")
        if not repo_data or not repo_data.get("defaultBranchRef"):
            break
        history = repo_data["defaultBranchRef"]["target"]["history"]
        for edge in history.get("edges", []):
            node = edge.get("node", {})
            user_ref = node.get("author", {}).get("user")
            if owner_id and user_ref and user_ref.get("id") == owner_id:
                my_commits += 1
                additions += node.get("additions", 0)
                deletions += node.get("deletions", 0)
        if history.get("pageInfo", {}).get("hasNextPage"):
            curr_cursor = history["pageInfo"]["endCursor"]
        else:
            break
    return additions, deletions, my_commits


def loc_query(
    owner_affiliation: List[str], comment_size: int = 7, owner_id: Optional[str] = None
) -> List[Any]:
    cache_dir = BASE_DIR / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        cache_dir / f"{hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest()}.txt"
    )

    if not ACCESS_TOKEN:
        return [8135255, 2582616, 5552639, True]

    query_count("loc_query")
    query = (
        """
    query ($cursor: String) {
        user(login: "%s") {
            repositories(first: 60, after: $cursor, ownerAffiliations: [OWNER, COLLABORATOR, ORGANIZATION_MEMBER]) {
                edges {
                    node {
                        nameWithOwner
                        defaultBranchRef {
                            target {
                                ... on Commit {
                                    history {
                                        totalCount
                                    }
                                }
                            }
                        }
                    }
                }
                pageInfo {
                    endCursor
                    hasNextPage
                }
            }
        }
    }"""
        % USER_NAME
    )

    edges = []
    cursor = None
    while True:
        req = post_graphql(query, {"cursor": cursor})
        if not req or req.status_code != 200:
            break
        data = req.json().get("data", {}).get("user", {}).get("repositories", {})
        edges.extend([e for e in data.get("edges", []) if e.get("node")])
        if data.get("pageInfo", {}).get("hasNextPage"):
            cursor = data["pageInfo"]["endCursor"]
        else:
            break

    if not edges:
        return [8135255, 2582616, 5552639, True]

    return cache_builder(edges, filename, comment_size, owner_id)


def cache_builder(
    edges: List[Any], filename: Path, comment_size: int, owner_id: Optional[str]
) -> List[Any]:
    cached = True
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = f.readlines()
    except FileNotFoundError:
        data = [f"Comment line {i}\n" for i in range(comment_size)]
        with open(filename, "w", encoding="utf-8") as f:
            f.writelines(data)

    cache_comment = data[:comment_size]
    data = data[comment_size:]

    cache_map = {}
    for line in data:
        parts = line.split()
        if len(parts) >= 5:
            cache_map[parts[0]] = parts

    new_data = []
    for edge in edges:
        name_with_owner = edge["node"]["nameWithOwner"]
        repo_hash = hashlib.sha256(name_with_owner.encode("utf-8")).hexdigest()
        branch = edge["node"].get("defaultBranchRef")

        if not branch:
            new_data.append(f"{repo_hash} 0 0 0 0\n")
            continue

        total_branch_commits = branch["target"]["history"]["totalCount"]

        if (
            repo_hash in cache_map
            and int(cache_map[repo_hash][1]) == total_branch_commits
        ):
            new_data.append(" ".join(cache_map[repo_hash]) + "\n")
        else:
            cached = False
            owner, repo_name = name_with_owner.split("/")
            adds, dels, my_c = recursive_loc(owner, repo_name, owner_id=owner_id)
            new_data.append(
                f"{repo_hash} {total_branch_commits} {my_c} {adds} {dels}\n"
            )

    with open(filename, "w", encoding="utf-8") as f:
        f.writelines(cache_comment)
        f.writelines(new_data)

    loc_add = 0
    loc_del = 0
    for line in new_data:
        parts = line.split()
        if len(parts) >= 5:
            loc_add += int(parts[3])
            loc_del += int(parts[4])

    return [loc_add, loc_del, loc_add - loc_del, cached]


def svg_overwrite(
    filename: Union[str, Path],
    age_data: str,
    commit_data: Any,
    star_data: Any,
    repo_data: Any,
    contrib_data: Any,
    follower_data: Any,
    loc_data: List[Any],
    highlights_data: List[Dict[str, Any]] = [],
    system_info_data: List[Dict[str, str]] = SYSTEM_INFO,
    proficiency_data: List[Dict[str, Union[str, int]]] = CORE_PROFICIENCY,
    connect_data: List[Dict[str, str]] = CONNECT_INFO,
    tech_stack_data: List[Dict[str, str]] = TECH_STACK,
) -> None:
    file_path = Path(filename)
    if not file_path.is_file():
        file_path = BASE_DIR / filename

    tree = etree.parse(str(file_path))
    root = tree.getroot()

    if len(system_info_data) > 0:
        format_field_row(
            root,
            system_info_data[0]["label"],
            system_info_data[0]["value"],
            "sys_label_0",
            "sys_dots_0",
            "sys_val_0",
            56,
        )
    format_dots_value(root, ". Uptime", "age_data", str(age_data), 56)
    for idx, item in enumerate(system_info_data[1:6], start=1):
        format_field_row(
            root,
            item["label"],
            item["value"],
            f"sys_label_{idx}",
            f"sys_dots_{idx}",
            f"sys_val_{idx}",
            56,
        )

    for idx, item in enumerate(proficiency_data[:8]):
        p_res = render_proficiency_item(
            item, total_width=56, bar_len=16, bar_start_col=32
        )
        find_and_replace(root, f"prof_name_{idx}", p_res["name"])
        find_and_replace(root, f"prof_dots_{idx}", p_res["dots"])
        find_and_replace(root, f"prof_fill_{idx}", p_res["fill"])
        find_and_replace(root, f"prof_empty_{idx}", p_res["empty"])
        find_and_replace(root, f"prof_val_{idx}", p_res["val"])

    for idx, item in enumerate(connect_data[:3]):
        format_field_row(
            root,
            item["label"],
            item["value"],
            f"conn_label_{idx}",
            f"conn_dots_{idx}",
            f"conn_val_{idx}",
            56,
        )

    for idx, item in enumerate(tech_stack_data[:7]):
        format_field_row(
            root,
            item["label"],
            item["value"],
            f"stack_label_{idx}",
            f"stack_dots_{idx}",
            f"stack_val_{idx}",
            57,
        )

    format_dots_value(root, ". Total Stars", "star_data", star_data, 57)
    format_dots_value(root, ". Total Commits", "commit_data", commit_data, 57)
    format_dots_value(root, ". Followers", "follower_data", follower_data, 57)
    format_dots_value(root, ". Lines of Code", "loc_data", loc_data[2], 57)

    add_val = (
        f"{loc_data[0]:,} ++" if isinstance(loc_data[0], int) else f"{loc_data[0]} ++"
    )
    del_val = (
        f"{loc_data[1]:,} --" if isinstance(loc_data[1], int) else f"{loc_data[1]} --"
    )
    format_dots_value(root, ".   Added (++)", "loc_add", add_val, 57)
    format_dots_value(root, ".   Deleted (--)", "loc_del", del_val, 57)

    repo_val = f"{repo_data:,}" if isinstance(repo_data, int) else str(repo_data)
    contrib_val = (
        f"{contrib_data:,}" if isinstance(contrib_data, int) else str(contrib_data)
    )
    format_dots_value(
        root,
        ". Repositories",
        "repo_data",
        f"{repo_val} {{Contributed: {contrib_val}}}",
        57,
    )
    find_and_replace(root, "repo_data", repo_val)
    find_and_replace(root, "contrib_data", contrib_val)

    for idx, hl in enumerate(highlights_data[:4]):
        raw_name = hl["name"]
        name_display = (raw_name[:20] + "…") if len(raw_name) > 21 else raw_name
        prefix = f". {name_display}"
        max_lang_len = max(8, 57 - len(prefix) - 4)
        lang_str = format_languages(hl.get("langs", []), max_lang_len)

        gap = 57 - len(prefix) - len(lang_str)
        dots = " " * max(0, gap) if gap <= 2 else " " + ("." * (gap - 2)) + " "

        find_and_replace(root, f"hl_name_{idx}", name_display)
        find_and_replace(root, f"hl_dots_{idx}", dots)
        find_and_replace(root, f"hl_desc_{idx}", lang_str)

    tree.write(str(file_path), encoding="utf-8", xml_declaration=True)


def perf_counter(funct, *args) -> Tuple[Any, float]:
    start = time.perf_counter()
    ret = funct(*args)
    return ret, time.perf_counter() - start


def format_duration(diff: float) -> str:
    return f"{diff:.4f} s" if diff > 1 else f"{diff * 1000:.2f} ms"


def update_readme() -> None:
    timestamp = int(time.time())
    readme_content = f"""<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="dark_mode.svg?v={timestamp}">
    <img alt="{USER_NAME}'s GitHub Profile README" src="light_mode.svg?v={timestamp}">
  </picture>

  <p align="center">
    <a href="mailto:adib23704@gmail.com"><img src="https://img.shields.io/badge/Email-adib23704%40gmail.com-ea4335?style=flat-square&logo=gmail&logoColor=white" alt="Email"/></a>
    &nbsp;
    <a href="https://linkedin.com/in/adib23704" target="_blank"><img src="https://img.shields.io/badge/LinkedIn-in%2Fadib23704-0077b5?style=flat-square&logo=linkedin&logoColor=white" alt="LinkedIn"/></a>
    &nbsp;
    <a href="https://adibdev.me" target="_blank"><img src="https://img.shields.io/badge/Portfolio-adibdev.me-0969da?style=flat-square&logo=googlechrome&logoColor=white" alt="Portfolio"/></a>
  </p>
</div>
"""
    readme_path = BASE_DIR / "README.md"
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(readme_content)


def main() -> None:
    user_data, user_time = perf_counter(user_getter, USER_NAME)
    owner_id = user_data[0].get("id")
    print(f"   ✓ User Account:       {format_duration(user_time)}")

    age_data, age_time = perf_counter(daily_readme, BIRTH_DATE)
    print(f"   ✓ Live Uptime:        {format_duration(age_time)}")

    total_loc, loc_time = perf_counter(
        loc_query, ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"], 7, owner_id
    )
    cache_status = "(cached)" if total_loc[-1] else "(fresh)"
    print(f"   ✓ Lines of Code {cache_status}: {format_duration(loc_time)}")

    commit_data, commit_time = perf_counter(commit_counter, 7)
    star_data, star_time = perf_counter(graph_repos_stars, "stars", ["OWNER"])
    repo_data, repo_time = perf_counter(graph_repos_stars, "repos", ["OWNER"])
    contrib_data, contrib_time = perf_counter(
        graph_repos_stars, "repos", ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"]
    )
    follower_data, follower_time = perf_counter(follower_getter, USER_NAME)

    highlights_data, hl_time = perf_counter(highlights_getter, FEATURED_REPOSITORIES)
    print(f"   ✓ Featured Repos:     {format_duration(hl_time)}")

    svg_overwrite(
        BASE_DIR / "dark_mode.svg",
        age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc[:3],
        highlights_data,
    )
    svg_overwrite(
        BASE_DIR / "light_mode.svg",
        age_data,
        commit_data,
        star_data,
        repo_data,
        contrib_data,
        follower_data,
        total_loc[:3],
        highlights_data,
    )
    update_readme()

    total_time = (
        user_time
        + age_time
        + loc_time
        + commit_time
        + star_time
        + repo_time
        + contrib_time
        + hl_time
    )
    print(f"\n✨ Dashboards updated successfully! Total time: {total_time:.4f}s")
    print(f"📡 Total GitHub GraphQL API calls: {sum(QUERY_COUNT.values())}\n")


if __name__ == "__main__":
    main()
