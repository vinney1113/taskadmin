import json
import re

from pytest_bdd import given, parsers, scenarios, then, when
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

scenarios("taskadmin.feature")


def make_task(title, start_date=None):
    return {
        "id": abs(hash(title)),
        "title": title,
        "completed": False,
        "createdAt": f"2026-07-31T12:00:00.000Z",
        "startDate": start_date,
    }


def seed_tasks(driver, tasks):
    driver.execute_script(
        "localStorage.setItem('tasks', arguments[0]);",
        json.dumps(tasks),
    )
    driver.refresh()


def task_from_storage(driver, title):
    tasks = driver.execute_script(
        "return JSON.parse(localStorage.getItem('tasks') || '[]');"
    )
    for task in tasks:
        if task["title"] == title:
            return task
    return None


def find_li_by_title(driver, title):
    for li in driver.find_elements(By.CSS_SELECTOR, "#task-list li"):
        spans = li.find_elements(By.CSS_SELECTOR, ".fw-medium")
        if spans and spans[0].text == title:
            return li
    return None


def color_of(li):
    cls = li.get_attribute("class") or ""
    match = re.search(r"text-bg-(\S+)", cls)
    return match.group(1) if match else None


def record_task(driver, context, title):
    task = task_from_storage(driver, title)
    context["created"][task["id"]] = task["createdAt"]
    li = find_li_by_title(driver, title)
    context["colors"][task["id"]] = color_of(li)


@given(parsers.parse('I have an existing task "{title}"'))
def existing_task(driver, context, title):
    seed_tasks(driver, [make_task(title)])
    record_task(driver, context, title)


@given(parsers.parse('I have an existing task "{title}" with start date "{date}"'))
def existing_task_with_date(driver, context, title, date):
    seed_tasks(driver, [make_task(title, start_date=date)])
    record_task(driver, context, title)


@given(parsers.parse('I have existing tasks "{t1}" and "{t2}"'))
def existing_tasks(driver, context, t1, t2):
    seed_tasks(driver, [make_task(t1), make_task(t2)])
    record_task(driver, context, t1)
    record_task(driver, context, t2)


@given(parsers.parse('I enter the task title "{title}"'))
def enter_title(driver, title):
    el = driver.find_element(By.ID, "title")
    el.clear()
    el.send_keys(title)


@given(parsers.parse('I set the start date to "{date}"'))
def set_start_date(driver, date):
    driver.execute_script(
        "document.getElementById('start-date').value = arguments[0];",
        date,
    )


@given("I leave the start date empty")
def leave_date_empty(driver):
    driver.find_element(By.ID, "start-date").clear()


@when("I submit the task")
def submit_task(driver):
    driver.find_element(By.CSS_SELECTOR, "#task-form button[type='submit']").click()


@when(parsers.parse('I create a task "{title}"'))
def create_task(driver, title):
    driver.find_element(By.ID, "title").send_keys(title)
    driver.find_element(By.CSS_SELECTOR, "#task-form button[type='submit']").click()


@when(parsers.re(r'I edit the task "(?P<old>[^"]*)" to "(?P<new>[^"]*)"'))
def edit_task(driver, old, new):
    li = find_li_by_title(driver, old)
    assert li is not None, f"task {old!r} not found"
    li.find_element(By.CSS_SELECTOR, "button[data-action='edit']").click()
    inp = WebDriverWait(driver, 5).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, ".edit-input"))
    )
    inp.clear()
    inp.send_keys(new)
    li.find_element(By.CSS_SELECTOR, "button[data-action='save']").click()


@when(parsers.parse('I mark "{title}" as completed'))
def mark_completed(driver, title):
    driver.execute_script(
        """
        const tasks = JSON.parse(localStorage.getItem('tasks') || '[]');
        const task = tasks.find(t => t.title === arguments[0]);
        if (task) task.completed = true;
        localStorage.setItem('tasks', JSON.stringify(tasks));
        """,
        title,
    )
    driver.refresh()


@then(parsers.parse('the task list shows "{title}"'))
def list_shows(driver, title):
    assert find_li_by_title(driver, title) is not None, f"task {title!r} not in list"


@then(parsers.parse('the task list should show "{title}"'))
def list_should_show(driver, title):
    assert find_li_by_title(driver, title) is not None, f"task {title!r} not in list"


@then(parsers.parse('the task list should not show "{title}"'))
def list_should_not_show(driver, title):
    assert find_li_by_title(driver, title) is None, f"task {title!r} still in list"


@then("an error message is shown")
def error_shown(driver):
    err = driver.find_element(By.ID, "error")
    assert err.is_displayed(), "error element is not visible"
    assert err.text.strip(), "error element has no message"


@then(parsers.parse('the task title remains "{title}"'))
def title_remains(driver, title):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["title"] == title


@then(parsers.parse('the task "{title}" remains completed'))
def remains_completed(driver, title):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["completed"] is True


@then(parsers.parse('the task "{title}" keeps its original creation date'))
def keeps_created_date(driver, context, title):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["createdAt"] == context["created"][task["id"]]


@then(parsers.parse('the task "{title}" shows start date "{date}"'))
def shows_start_date(driver, title, date):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["startDate"] == date


@then(parsers.parse('the task "{title}" keeps its start date "{date}"'))
def keeps_start_date(driver, title, date):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert task["startDate"] == date


@then(parsers.parse('the task "{title}" has no start date'))
def has_no_start_date(driver, title):
    task = task_from_storage(driver, title)
    assert task is not None, f"task {title!r} not found"
    assert not task.get("startDate")


@then(parsers.parse('the task "{title}" is assigned a color'))
def assigned_color(driver, title):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not in list"
    assert color_of(li), f"task {title!r} has no color"


@then(parsers.parse('the task "{title}" keeps its color'))
@then(parsers.parse('the task "{title}" keeps its original color'))
def keeps_color(driver, context, title):
    li = find_li_by_title(driver, title)
    assert li is not None, f"task {title!r} not in list"
    task = task_from_storage(driver, title)
    assert color_of(li) == context["colors"][task["id"]]


@then("no two tasks share the same color")
def unique_colors(driver):
    colors = [
        color_of(li)
        for li in driver.find_elements(By.CSS_SELECTOR, "#task-list li")
    ]
    assert len(colors) == len(set(colors)), f"duplicate colors found: {colors}"
