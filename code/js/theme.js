/*!
 * theme.js — کلید حالت روشن/تاریک برای بازی و صفحه‌ی معرفی (نسخه ۶.۳.۰)
 *
 * پیش‌فرض: روشن. انتخاب کاربر در localStorage (کلید chalesh-gamma-theme) ذخیره می‌شود.
 * اعمال: ویژگی data-theme="dark" روی <html>؛ توکن‌های رنگ در style.css و intro/intro.css
 * این ویژگی را می‌خوانند. تغییر حالت:
 *   - مرورگرهای با View Transitions: دایره‌ای از محل کلید گسترده می‌شود.
 *   - بقیه: گذار رنگ کوتاه روی کل صفحه (کلاس theme-fade).
 *   - کاهش حرکت: تغییر آنی.
 * هر تغییر رویداد «chalesh:theme» را منتشر می‌کند تا بوم صحنه‌ها رنگ‌هایش را دوباره بخواند.
 *
 * این فایل باید در <head> و پیش از استایل‌ها بارگذاری شود تا صفحه بین دو حالت نپرد.
 */
(function (global) {
  'use strict';

  var KEY = 'chalesh-gamma-theme';
  var root = document.documentElement;
  var reduce = !!(global.matchMedia && global.matchMedia('(prefers-reduced-motion: reduce)').matches);

  function stored() {
    try { return global.localStorage.getItem(KEY); } catch (e) { return null; }
  }

  function apply(name) {
    if (name === 'dark') root.setAttribute('data-theme', 'dark');
    else root.removeAttribute('data-theme');
  }

  function current() {
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  /** کلید را با حالت واقعی صفحه همگام می‌کند. */
  function sync() {
    var input = document.getElementById('theme-toggle');
    if (!input) return;
    var dark = current() === 'dark';
    input.checked = dark;
    input.setAttribute('aria-checked', dark ? 'true' : 'false');
  }

  function commit(next) {
    apply(next);
    try { global.localStorage.setItem(KEY, next); } catch (e) { /* حافظه در دسترس نیست: فقط همین نشست */ }
    sync();
    global.dispatchEvent(new CustomEvent('chalesh:theme', { detail: next }));
  }

  /** مرکز عنصر کلید، به‌عنوان مبدأ انیمیشن دایره‌ای. */
  function originOf(el) {
    var r = el ? el.getBoundingClientRect() : null;
    if (!r || (r.width === 0 && r.height === 0)) return { x: global.innerWidth - 40, y: 40 };
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }

  /** تغییر حالت با انیمیشن. origin: نقطه‌ی شروع دایره (اختیاری). */
  function set(name, origin) {
    var next = name === 'dark' ? 'dark' : 'light';
    if (next === current()) { sync(); return; }
    var o = origin || originOf(document.querySelector('.trigger--theme'));

    if (!reduce && document.startViewTransition) {
      var maxR = Math.hypot(Math.max(o.x, global.innerWidth - o.x), Math.max(o.y, global.innerHeight - o.y));
      var vt = document.startViewTransition(function () { commit(next); });
      vt.ready.then(function () {
        root.animate(
          { clipPath: ['circle(0px at ' + o.x + 'px ' + o.y + 'px)', 'circle(' + maxR + 'px at ' + o.x + 'px ' + o.y + 'px)'] },
          { duration: 750, easing: 'cubic-bezier(0.2, 0.7, 0.2, 1)', pseudoElement: '::view-transition-new(root)' }
        );
      }).catch(function () { /* انیمیشن لغو شد: حالت تغییر کرده است */ });
    } else if (!reduce) {
      root.classList.add('theme-fade');
      commit(next);
      global.setTimeout(function () { root.classList.remove('theme-fade'); }, 700);
    } else {
      commit(next);
    }
  }

  // اعمال فوری حالت ذخیره‌شده (پیش از رندر)
  apply(stored() === 'dark' ? 'dark' : 'light');

  document.addEventListener('DOMContentLoaded', function () {
    sync();
    var input = document.getElementById('theme-toggle');
    if (input) {
      input.addEventListener('change', function (e) {
        var label = e.target.closest('.trigger') || e.target;
        set(e.target.checked ? 'dark' : 'light', originOf(label));
      });
    }
  });

  global.ChaleshTheme = { current: current, set: set };
})(window);
