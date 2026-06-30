/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { Dialog } from '@web/core/dialog/dialog';
import { useService } from '@web/core/utils/hooks';
import { onMounted, onWillUnmount } from '@odoo/owl';

const MIN_W = 420;
const MIN_H = 180;

function uidForDialog(props) {
    return props?.title || props?.bodyId || 'odoo_dialog_default';
}

patch(Dialog.prototype, 'odoo_dialog_user_layout.patch', {
    setup() {
        this._super(...arguments);
        this.rpc = useService('rpc');
        this.notification = useService('notification');
        this._dragState = null;
        this._resizeState = null;

        onMounted(() => {
            this.el = this.el || this.root?.el || document.querySelector('.modal.show');
            if (!this.el) return;
            this._applySavedLayout();
            this._bindEvents();
        });

        onWillUnmount(() => {
            this._unbindEvents();
        });
    },

    async _applySavedLayout() {
        const key = uidForDialog(this.props);
        const layout = await this.rpc('/odoo_dialog_user_layout/get', { key });
        const modal = this.el.querySelector('.modal-dialog') || this.el;
        if (!layout || Object.keys(layout).length === 0) return;
        if (layout.width) modal.style.width = `${layout.width}px`;
        if (layout.height) modal.style.height = `${layout.height}px`;
        if (layout.left != null) modal.style.left = `${layout.left}px`;
        if (layout.top != null) modal.style.top = `${layout.top}px`;
        modal.style.position = 'fixed';
        modal.style.margin = '0';
    },

    _bindEvents() {
        const modal = this.el.querySelector('.modal-dialog') || this.el;
        const header = this.el.querySelector('.modal-header');
        if (!modal || !header) return;
        this._modalEl = modal;
        this._headerEl = header;
        this._onDown = (ev) => this._startDrag(ev);
        this._onMove = (ev) => this._onPointerMove(ev);
        this._onUp = () => this._stopPointer();
        header.style.cursor = 'move';
        header.addEventListener('pointerdown', this._onDown);
        document.addEventListener('pointermove', this._onMove);
        document.addEventListener('pointerup', this._onUp);

        const handle = document.createElement('div');
        handle.className = 'odoo-dialog-resize-handle';
        modal.appendChild(handle);
        handle.addEventListener('pointerdown', (ev) => this._startResize(ev));
    },

    _unbindEvents() {
        if (this._headerEl && this._onDown) this._headerEl.removeEventListener('pointerdown', this._onDown);
        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
    },

    _startDrag(ev) {
        if (ev.target.closest('.btn, .close, button, input, textarea, select, a')) return;
        const rect = this._modalEl.getBoundingClientRect();
        this._dragState = { x: ev.clientX, y: ev.clientY, left: rect.left, top: rect.top };
        this._modalEl.style.position = 'fixed';
        this._modalEl.style.margin = '0';
        ev.preventDefault();
    },

    _startResize(ev) {
        const rect = this._modalEl.getBoundingClientRect();
        this._resizeState = { x: ev.clientX, y: ev.clientY, width: rect.width, height: rect.height };
        ev.preventDefault();
        ev.stopPropagation();
    },

    _onPointerMove(ev) {
        if (this._dragState) {
            const dx = ev.clientX - this._dragState.x;
            const dy = ev.clientY - this._dragState.y;
            this._modalEl.style.left = `${this._dragState.left + dx}px`;
            this._modalEl.style.top = `${this._dragState.top + dy}px`;
        }
        if (this._resizeState) {
            const dw = ev.clientX - this._resizeState.x;
            const dh = ev.clientY - this._resizeState.y;
            this._modalEl.style.width = `${Math.max(MIN_W, this._resizeState.width + dw)}px`;
            this._modalEl.style.height = `${Math.max(MIN_H, this._resizeState.height + dh)}px`;
        }
    },

    _stopPointer() {
        if (this._dragState || this._resizeState) this._saveLayout();
        this._dragState = null;
        this._resizeState = null;
    },

    async _saveLayout() {
        const key = uidForDialog(this.props);
        const rect = this._modalEl.getBoundingClientRect();
        await this.rpc('/odoo_dialog_user_layout/set', {
            key,
            values: { left: Math.round(rect.left), top: Math.round(rect.top), width: Math.round(rect.width), height: Math.round(rect.height) },
        });
    },
});
