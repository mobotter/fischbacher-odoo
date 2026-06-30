/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { Dialog } from '@web/core/dialog/dialog';
import { rpc } from '@web/core/network/rpc';
import { onMounted, onWillUnmount, onRendered } from '@odoo/owl';

function layoutKey(props) {
    return props?.title || props?.bodyId || props?.className || 'default_dialog';
}

patch(Dialog.prototype, {
    setup() {
        super.setup(...arguments);
        this._drag = null;
        this._resize = null;
        this._handleObserver = null;
        onMounted(() => this._initDialog());
        onRendered(() => this._ensureResizeHandle());
        onWillUnmount(() => this._cleanup());
    },

    async _fetchLayout(key) {
        return await rpc('/odoo_dialog_user_layout/get', { key });
    },

    async _saveLayout(key, values) {
        return await rpc('/odoo_dialog_user_layout/set', { key, values });
    },

    async _resetLayout(key) {
        return await rpc('/odoo_dialog_user_layout/reset', { key });
    },

    async _initDialog() {
        const root = this.el;
        this.dialogEl = root?.querySelector('.modal-content.o_select_create_dialog_content') || root?.querySelector('.modal-content');
        this.contentEl = this.dialogEl;
        if (!this.dialogEl) return;

        this.dialogEl.classList.add('odoo-dialog-resizable');
        this.dialogEl.style.position = 'relative';
        this.dialogEl.style.margin = '0';
        this.dialogEl.style.maxWidth = 'none';
        this.dialogEl.style.overflow = 'visible';

        const key = layoutKey(this.props);
        const layout = await this._fetchLayout(key);
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

        this._ensureHeaderBindings();
        this._ensureResizeHandle();

        if (this._handleObserver) this._handleObserver.disconnect();
        this._handleObserver = new MutationObserver(() => this._ensureResizeHandle());
        this._handleObserver.observe(this.dialogEl, { childList: true, subtree: false });
    },

    _ensureHeaderBindings() {
        const header = this.el?.querySelector('.modal-header');
        if (!header) return;

        if (!this._onHeaderDown) {
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
                const key = layoutKey(this.props);
                await this._resetLayout(key);
                location.reload();
            });
            header.appendChild(btn);
        }
    },

    _ensureResizeHandle() {
        console.log('ensure handle', this.dialogEl);
        if (!this.dialogEl) return;
    
        let footer = this.dialogEl.querySelector('.modal-footer');
        if (!footer) {
            footer = document.createElement('div');
            footer.className = 'modal-footer odoo-dialog-resize-footer';
            this.dialogEl.appendChild(footer);
        }
    
        const existing = footer.querySelector('.odoo-dialog-resize-handle');
        if (existing) {
            this._resizeHandle = existing;
            return;
        }
    
        this._resizeHandle = document.createElement('div');
        this._resizeHandle.className = 'odoo-dialog-resize-handle';
        this._resizeHandle.style.background = 'red';
        footer.appendChild(this._resizeHandle);
    
        this._onResizeDown = (ev) => this._startResize(ev);
        this._resizeHandle.addEventListener('pointerdown', this._onResizeDown);
    
        console.log('handle added', this._resizeHandle);
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
        if (this._handleObserver) this._handleObserver.disconnect();
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
        ev.preventDefault();
        ev.stopPropagation();
        ev.stopImmediatePropagation?.();
        const r = this.dialogEl.getBoundingClientRect();
        this._resize = { x: ev.clientX, y: ev.clientY, width: r.width, height: r.height };
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
            await this._saveLayout(key, {
                left: Math.round(r.left),
                top: Math.round(r.top),
                width: Math.round(r.width),
                height: Math.round(r.height),
                maximized: false,
            });
        }
        this._drag = null;
        this._resize = null;
    },
});
