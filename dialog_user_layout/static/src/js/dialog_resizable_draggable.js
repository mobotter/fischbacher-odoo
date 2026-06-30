/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { Dialog } from '@web/core/dialog/dialog';
import { useService } from '@web/core/utils/hooks';
import { onMounted, onWillUnmount } from '@odoo/owl';

function layoutKey(props) {
    return props?.title || props?.bodyId || props?.className || 'default_dialog';
}

patch(Dialog.prototype, 'odoo_dialog_user_layout_v4', {
    setup() {
        this._super(...arguments);
        this.rpc = useService('rpc');
        this._drag = null;
        this._resize = null;
        onMounted(() => this._initDialog());
        onWillUnmount(() => this._cleanup());
    },

    async _initDialog() {
        this.dialogEl = this.el?.querySelector('.modal-dialog') || this.el;
        this.contentEl = this.el?.querySelector('.modal-content') || this.dialogEl;
        if (!this.dialogEl || !this.contentEl) return;

        this.dialogEl.classList.add('odoo-dialog-draggable-resizable');
        this.dialogEl.style.position = 'fixed';
        this.dialogEl.style.margin = '0';
        this.dialogEl.style.maxWidth = 'none';
        this.contentEl.style.overflow = 'visible';

        const key = layoutKey(this.props);
        const layout = await this.rpc('/odoo_dialog_user_layout/get', { key });
        const v = layout && layout[key];
        if (v) {
            if (v.maximized) {
                this._maximize();
            } else {
                if (v.width) this.dialogEl.style.width = `${v.width}px`;
                if (v.height) this.dialogEl.style.height = `${v.height}px`;
                if (v.left != null) this.dialogEl.style.left = `${v.left}px`;
                if (v.top != null) this.dialogEl.style.top = `${v.top}px`;
            }
        }

        const header = this.el?.querySelector('.modal-header');
        if (header) {
            header.style.cursor = 'move';
            this._onHeaderDown = (ev) => this._startDrag(ev);
            header.addEventListener('pointerdown', this._onHeaderDown);

            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = 'btn btn-secondary btn-sm odoo-dialog-reset-btn';
            btn.textContent = '↺';
            btn.title = 'Reset layout';
            btn.addEventListener('click', async (e) => {
                e.stopPropagation();
                await this.rpc('/odoo_dialog_user_layout/reset', { key });
                location.reload();
            });
            header.appendChild(btn);
        }

        this._resizeHandle = document.createElement('div');
        this._resizeHandle.className = 'odoo-dialog-resize-handle';
        this.dialogEl.appendChild(this._resizeHandle);

        this._onResizeDown = (ev) => this._startResize(ev);
        this._resizeHandle.addEventListener('pointerdown', this._onResizeDown);

        this._onMove = (ev) => this._move(ev);
        this._onUp = () => this._stop();
        document.addEventListener('pointermove', this._onMove);
        document.addEventListener('pointerup', this._onUp);
    },

    _maximize() {
        this.dialogEl.style.left = '0px';
        this.dialogEl.style.top = '0px';
        this.dialogEl.style.width = '100vw';
        this.dialogEl.style.height = '100vh';
    },

    _cleanup() {
        const header = this.el?.querySelector('.modal-header');
        if (header && this._onHeaderDown) header.removeEventListener('pointerdown', this._onHeaderDown);
        if (this._resizeHandle && this._onResizeDown) this._resizeHandle.removeEventListener('pointerdown', this._onResizeDown);
        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
    },

    _startDrag(ev) {
        if (ev.target.closest('button,a,input,textarea,select')) return;
        const r = this.dialogEl.getBoundingClientRect();
        this._drag = { x: ev.clientX, y: ev.clientY, left: r.left, top: r.top };
        ev.preventDefault();
    },

    _startResize(ev) {
        const r = this.dialogEl.getBoundingClientRect();
        this._resize = { x: ev.clientX, y: ev.clientY, width: r.width, height: r.height };
        ev.preventDefault();
        ev.stopPropagation();
    },

    _move(ev) {
        if (this._drag) {
            this.dialogEl.style.left = `${this._drag.left + (ev.clientX - this._drag.x)}px`;
            this.dialogEl.style.top = `${this._drag.top + (ev.clientY - this._drag.y)}px`;
        }
        if (this._resize) {
            this.dialogEl.style.width = `${Math.max(420, this._resize.width + (ev.clientX - this._resize.x))}px`;
            this.dialogEl.style.height = `${Math.max(180, this._resize.height + (ev.clientY - this._resize.y))}px`;
        }
    },

    async _stop() {
        if (this.dialogEl && (this._drag || this._resize)) {
            const r = this.dialogEl.getBoundingClientRect();
            const key = layoutKey(this.props);
            await this.rpc('/odoo_dialog_user_layout/set', {
                key,
                values: {
                    left: Math.round(r.left),
                    top: Math.round(r.top),
                    width: Math.round(r.width),
                    height: Math.round(r.height),
                    maximized: false,
                },
            });
        }
        this._drag = null;
        this._resize = null;
    },
});
