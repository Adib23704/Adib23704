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
    "https://github.com/Adib23704/completeDiscordQuest-Vencord",
    "https://github.com/Adib23704/autoReactor-Vencord",
    "https://github.com/Adib23704/devCompanionExtended-Vencord",
]

ACCESS_TOKEN = os.environ.get("ACCESS_TOKEN", "").strip()
HEADERS = {"authorization": f"token {ACCESS_TOKEN}"} if ACCESS_TOKEN else {}
USER_NAME = os.environ.get("USER_NAME", "Adib23704").strip()

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
    """Execute a GraphQL query against GitHub's API with exponential backoff for transient errors."""
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
    print(f"   [Notice] {func_name} GraphQL request ({status})")
    return res


def find_and_replace(root: etree._Element, element_id: str, new_text: str) -> None:
    """Finds an SVG element by its ID and updates its text content."""
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
    """Formats a key-value row with leader dots to fit the exact column width."""
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
    """Formats single element values (e.g. Uptime, Stars, Commits) with leader dots."""
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
    """Dynamically calculates ASCII progress bar blocks and leader dots for a skill."""
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
    """Extracts (owner, repo_name) from URL or dictionary."""
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
    """Fetches all languages used in a repository in order of byte size."""
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
    """Packs languages separated by commas so they never exceed the max column width."""
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
    """Fetches repository names and language tags for featured repositories."""
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
    """Returns the live time duration since birthday (e.g. '22 years, 1 month, 7 days')."""
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
        return {"id": data.get("id", "")}, data.get("createdAt", "")
    return {"id": ""}, "2020-01-01T00:00:00Z"


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
    req = simple_request(follower_getter.__name__, query, {"login": username})
    if req and req.status_code == 200:
        return int(
            req.json()
            .get("data", {})
            .get("user", {})
            .get("followers", {})
            .get("totalCount", 0)
        )
    return 10


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
    req = simple_request(
        graph_repos_stars.__name__,
        query,
        {"owner_affiliation": owner_affiliation, "login": USER_NAME, "cursor": cursor},
    )
    if req and req.status_code == 200:
        repos_data = req.json().get("data", {}).get("user", {}).get("repositories", {})
        if count_type == "repos":
            return repos_data.get("totalCount", 0)
        elif count_type == "stars":
            total_stars = 0
            for edge in repos_data.get("edges", []):
                if edge.get("node") and "stargazers" in edge["node"]:
                    total_stars += edge["node"]["stargazers"].get("totalCount", 0)
            return total_stars
    return 30 if count_type == "repos" else 15


def commit_counter(comment_size: int = 7) -> int:
    """Reads total commits from the persistent SHA256 cache file."""
    cache_path = (
        BASE_DIR
        / "cache"
        / f"{hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest()}.txt"
    )
    if not cache_path.is_file():
        return 1250

    total = 0
    try:
        with open(cache_path, "r", encoding="utf-8") as f:
            lines = f.readlines()[comment_size:]
        for line in lines:
            parts = line.split()
            if len(parts) >= 3 and parts[2].isdigit():
                total += int(parts[2])
    except Exception:
        return 1250
    return total if total > 0 else 1250


def recursive_loc(
    owner: str,
    repo_name: str,
    data: List[str],
    cache_comment: List[str],
    addition_total: int = 0,
    deletion_total: int = 0,
    my_commits: int = 0,
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
                                haNextPage: hasNextPage
                            }
                        }
                    }
                }
            }
        }
    }"""
    req = post_graphql(
        query, {"repo_name": repo_name, "owner": owner, "cursor": cursor}
    )
    if req and req.status_code == 200:
        branch_ref = (
            req.json().get("data", {}).get("repository", {}).get("defaultBranchRef")
        )
        if branch_ref:
            history = branch_ref.get("target", {}).get("history", {})
            for edge in history.get("edges", []):
                node = edge.get("node", {})
                author_user = node.get("author", {}).get("user", {})
                if owner_id and author_user and author_user.get("id") == owner_id:
                    my_commits += 1
                    addition_total += node.get("additions", 0)
                    deletion_total += node.get("deletions", 0)
            if history.get("pageInfo", {}).get("haNextPage"):
                return recursive_loc(
                    owner,
                    repo_name,
                    data,
                    cache_comment,
                    addition_total,
                    deletion_total,
                    my_commits,
                    history["pageInfo"]["endCursor"],
                    owner_id,
                )
            return addition_total, deletion_total, my_commits
    return addition_total, deletion_total, my_commits


def loc_query(
    owner_affiliation: List[str], comment_size: int = 7, owner_id: Optional[str] = None
) -> List[Any]:
    """Queries repository lines of code differences using cached state."""
    cache_dir = BASE_DIR / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    filename = (
        cache_dir / f"{hashlib.sha256(USER_NAME.encode('utf-8')).hexdigest()}.txt"
    )

    if not ACCESS_TOKEN:
        return [150000, 20000, 130000, True]

    query_count("loc_query")
    query = """
    query ($owner_affiliation: [RepositoryAffiliation], $login: String!, $cursor: String) {
        user(login: $login) {
            repositories(first: 60, after: $cursor, ownerAffiliations: $owner_affiliation) {
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
    req = simple_request(
        "loc_query",
        query,
        {"owner_affiliation": owner_affiliation, "login": USER_NAME, "cursor": None},
    )
    if not req or req.status_code != 200:
        return [150000, 20000, 130000, True]

    edges = [
        e
        for e in req.json()
        .get("data", {})
        .get("user", {})
        .get("repositories", {})
        .get("edges", [])
        if e.get("node")
    ]

    try:
        with open(filename, "r", encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        lines = [f"Comment block line {i}\n" for i in range(comment_size)]

    cache_comment = lines[:comment_size]
    data = lines[comment_size:]

    loc_add = 0
    loc_del = 0
    for line in data:
        parts = line.split()
        if len(parts) >= 5:
            loc_add += int(parts[3])
            loc_del += int(parts[4])

    return [loc_add or 150000, loc_del or 20000, (loc_add - loc_del) or 130000, True]


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


def main() -> None:
    if not ACCESS_TOKEN:
        print(
            "💡 [Notice] Running without ACCESS_TOKEN. Using fallback / cached metrics."
        )

    user_data, user_time = perf_counter(user_getter, USER_NAME)
    owner_id = user_data[0].get("id")
    print(f"   ✓ User Account:       {format_duration(user_time)}")

    age_data, age_time = perf_counter(daily_readme, BIRTH_DATE)
    print(f"   ✓ Live Uptime:        {format_duration(age_time)}")

    total_loc, loc_time = perf_counter(
        loc_query, ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"], 7, owner_id
    )
    print(f"   ✓ Lines of Code:      {format_duration(loc_time)}")

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
    print(f"\nDashboards updated successfully! Total time: {total_time:.4f}s")
    print(f"Total GitHub GraphQL API calls: {sum(QUERY_COUNT.values())}\n")


if __name__ == "__main__":
    main()
