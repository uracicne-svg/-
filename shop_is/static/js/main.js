document.querySelectorAll('.toast').forEach(t => {
setTimeout(() => {
t.style.transition = 'opacity .4s, transform .4s';
t.style.opacity = '0';
t.style.transform = 'translateY(12px)';
setTimeout(() => t.remove(), 400);
}, 3500);
});
class Slider {
constructor(el) {
this.el = el;
this.track = el.querySelector('.slider__track');
this.slides = el.querySelectorAll('.slider__slide');
this.dots = el.querySelectorAll('.slider__dot');
this.total = this.slides.length;
this.current = 0;
this.timer = null;
el.querySelector('.slider__btn--prev')
?.addEventListener('click', () => this.prev());
el.querySelector('.slider__btn--next')
?.addEventListener('click', () => this.next());
this.dots.forEach((d, i) =>
d.addEventListener('click', () => this.goTo(i)));
this.start();
el.addEventListener('mouseenter', () => this.stop());
el.addEventListener('mouseleave', () => this.start());
}
goTo(idx) {
this.current = (idx + this.total) % this.total;
this.track.style.transform = `translateX(-${this.current * 100}%)`;
this.dots.forEach((d, i) =>
d.classList.toggle('active', i === this.current));
}
next() { this.goTo(this.current + 1); }
prev() { this.goTo(this.current - 1); }
start() {
this.stop();
this.timer = setInterval(() => this.next(), 3000);
}
stop() { clearInterval(this.timer); }
}
document.querySelectorAll('.slider').forEach(el => new Slider(el));
document.querySelectorAll('.table tbody tr').forEach(row => {
row.addEventListener('mouseenter', () => {
row.style.transition = 'background 160ms ease';
});
});
document.querySelectorAll('.btn').forEach(btn => {
btn.addEventListener('click', function (e) {
const rect = this.getBoundingClientRect();
const ripple = document.createElement('span');
const size = Math.max(rect.width, rect.height);
ripple.style.cssText = `
position:absolute; border-radius:50%;
width:${size}px; height:${size}px;
left:${e.clientX - rect.left - size/2}px;
top:${e.clientY - rect.top - size/2}px;
background:rgba(255,255,255,.18);
transform:scale(0); animation:ripple .5s ease-out forwards;
pointer-events:none;
`;
this.style.position = 'relative';
this.style.overflow = 'hidden';
this.appendChild(ripple);
ripple.addEventListener('animationend', () => ripple.remove());
});
});
const style = document.createElement('style');
style.textContent = `@keyframes ripple{to{transform:scale(2.5);opacity:0}}`;
document.head.appendChild(style);
document.querySelectorAll('.form-input').forEach(input => {
const group = input.closest('.form-group');
if (!group) return;
input.addEventListener('focus', () => {
group.style.transform = 'translateY(-1px)';
group.style.transition = 'transform 160ms ease';
});
input.addEventListener('blur', () => {
group.style.transform = '';
});
});
document.querySelectorAll('select[name="status"]').forEach(sel => {
function updateColor() {
const map = {
pending: '#8b90a7', confirmed: '#5b8af5',
shipped: '#f5a623', delivered: '#3ddc84',
cancelled: '#e05353'
};
sel.style.borderColor = map[sel.value] || '';
sel.style.color = map[sel.value] || '';
}
updateColor();
sel.addEventListener('change', updateColor);
});