/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { rpc } from '@web/core/network/rpc';
import { FormController } from '@web/views/form/form_controller';
import { onMounted, onWillUnmount, onRendered } from '@odoo/owl';
import { SelectCreateDialog } from '@web/views/view_dialogs/select_create_dialog';

function layoutKey(props) {
    return props?.title || props?.bodyId || props?.className || 'default_dialog';
}

function dbg(scope, ...args) {
    console.log(`[odoo-dialog:${scope}]`, ...args);
}

function sleepFrame() {
    return new Promise((resolve) => requestAnimationFrame(resolve));
}

function clamp(n, min, max) {
    return Math.min(max, Math.max(min, n));
}

async function resetLayoutKey(key) {
    await rpc('/odoo_dialog_user_layout/reset', { key });
}

patch(FormController.prototype, {
    async onResetDialogLayouts() {
        await resetLayoutKey('default_dialog');
        location.reload();
    },
});

patch(SelectCreateDialog.prototype, {
    setup() {
        super.setup(...arguments);

        this._drag = null;
        this._resize = null;
        this._handleObserver = null;
        this._onMove = null;
        this._onUp = null;
        this._onCancel = null;
        this._onHeaderDown = null;
        this._onResizeDown = null;
        this._resizeHandle = null;
        this._isMounted = false;

        dbg('SelectCreateDialog', 'setup', this.props);
        onMounted(() => {
            this._isMounted = true;
            this._initDialog();
        });
        onRendered(() => this._ensureResizeHandle());
        onWillUnmount(() => this._cleanup());
    },

    async _waitForDialogRoot(retries = 30) {
        for (let i = 0; i < retries; i++) {
            const found = document.querySelector('.modal-content.o_select_create_dialog_content')
                || document.querySelector('.modal-content')
                || document.querySelector('.modal-dialog');
            if (found) return found;
            await sleepFrame();
        }
        return null;
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
        if (!this._isMounted) return;

        this.dialogEl = await this._waitForDialogRoot();
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

        if (v && !v.maximized) {
            const vpW = window.innerWidth;
            const vpH = window.innerHeight;
            const width = v.width || 980;
            const height = v.height || 600;
            const maxW = Math.max(320, vpW - 20);
            const maxH = Math.max(240, vpH - 20);

            this.dialogEl.style.width = `${Math.min(width, maxW)}px`;
            this.dialogEl.style.height = `${Math.min(height, maxH)}px`;
            this.dialogEl.style.left = `${clamp(v.left ?? 0, 0, Math.max(0, vpW - 50))}px`;
            this.dialogEl.style.top = `${clamp(v.top ?? 0, 0, Math.max(0, vpH - 50))}px`;
        }

        if (v?.maximized) this._maximize();

        this._ensureHeaderBindings();
        this._ensureResizeHandle();

        if (this._handleObserver) this._handleObserver.disconnect();
        this._handleObserver = new MutationObserver(() => this._ensureResizeHandle());
        this._handleObserver.observe(this.dialogEl, { childList: true, subtree: false });
    },

    _ensureHeaderBindings() {
        const title = document.querySelector('.modal-title');
        if (!title || this._onHeaderDown) return;

        title.style.cursor = 'move';
        title.style.userSelect = 'none';
        title.style.touchAction = 'none';

        this._onHeaderDown = (ev) => this._startDrag(ev);
        title.addEventListener('pointerdown', this._onHeaderDown);

        const header = document.querySelector('.modal-header');
        if (header && !header.querySelector('.odoo-dialog-reset-btn')) {
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
        this._resizeHandle.textContent = '↘';
        footer.appendChild(this._resizeHandle);

        this._onResizeDown = (ev) => this._startResize(ev);
        this._resizeHandle.addEventListener('pointerdown', this._onResizeDown);
    },

    _maximize() {
        this.dialogEl.style.left = '0px';
        this.dialogEl.style.top = '0px';
        this.dialogEl.style.width = '100vw';
        this.dialogEl.style.height = '100vh';
    },

    _prepareDragBase() {
        const rect = this.dialogEl.getBoundingClientRect();
        const style = this.dialogEl.style;
        style.position = 'relative';
        style.margin = '0';
        style.willChange = 'left, top';
        return rect;
    },

    _cleanup() {
        const title = document.querySelector('.modal-title');
        if (title && this._onHeaderDown) title.removeEventListener('pointerdown', this._onHeaderDown);
        if (this._resizeHandle && this._onResizeDown) this._resizeHandle.removeEventListener('pointerdown', this._onResizeDown);
        if (this._handleObserver) this._handleObserver.disconnect();
        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
        if (this._onCancel) document.removeEventListener('pointercancel', this._onCancel);
    },

    _startDrag(ev) {
        const rect = this.dialogEl.getBoundingClientRect();
        console.log('dragstart', {
            clientX: ev.clientX,
            clientY: ev.clientY,
            rectLeft: rect.left,
            rectTop: rect.top,
            rectWidth: rect.width,
            rectHeight: rect.height,
        });
    
        this._drag = {
            pointerX: ev.clientX,
            pointerY: ev.clientY,
            offsetX: ev.clientX - rect.left,
            offsetY: ev.clientY - rect.top,
            pointerId: ev.pointerId,
            target: ev.currentTarget,
            ready: false,
        };
    
        ev.preventDefault();
        ev.stopPropagation();
        ev.currentTarget.setPointerCapture?.(ev.pointerId);
    
        requestAnimationFrame(() => {
            console.log('drag ready');
            if (this._drag) this._drag.ready = true;
        });
    
        this._bindMove();
    },

    _startResize(ev) {
        ev.preventDefault();
        ev.stopPropagation();
        ev.stopImmediatePropagation?.();
    
        const r = this.dialogEl.getBoundingClientRect();
        this._resize = {
            pointerX: ev.clientX,
            pointerY: ev.clientY,
            width: r.width,
            height: r.height,
            pointerId: ev.pointerId,
            target: ev.currentTarget,
        };
        this._drag = null;
    
        ev.currentTarget.setPointerCapture?.(ev.pointerId);
        this._bindMove();
    },


    _bindMove() {
        if (this._onMove) return;
        this._onMove = (e) => this._move(e);
        this._onUp = (e) => this._stop(e);
        this._onCancel = (e) => this._stop(e);
        document.addEventListener('pointermove', this._onMove);
        document.addEventListener('pointerup', this._onUp, { once: true });
        document.addEventListener('pointercancel', this._onCancel, { once: true });
    },

        _move(ev) {
            if (!this.dialogEl) return;
        
            if (this._drag) {
                if (!this._drag.ready) return;
        
                const x = ev.clientX - this._drag.offsetX;
                const y = ev.clientY - this._drag.offsetY;
        
                console.log('move', {
                    clientX: ev.clientX,
                    clientY: ev.clientY,
                    x,
                    y,
                });
        
                this.dialogEl.style.left = `${Math.max(0, x)}px`;
                this.dialogEl.style.top = `${Math.max(0, y)}px`;
            }
        },

    async _stop(ev) {
        const active = this._drag || this._resize;
        const target = active?.target;
        const pointerId = active?.pointerId;

        if (target && pointerId != null) {
            try {
                if (target.hasPointerCapture?.(pointerId)) {
                    target.releasePointerCapture(pointerId);
                }
            } catch (_) {}
        }

        if (this.dialogEl && active) {
            const r = this.dialogEl.getBoundingClientRect();
            const key = layoutKey(this.props);
            await this._saveLayout(key, {
                left: Math.round(clamp(r.left, 0, Math.max(0, window.innerWidth - r.width))),
                top: Math.round(clamp(r.top, 0, Math.max(0, window.innerHeight - r.height))),
                width: Math.round(Math.min(r.width, window.innerWidth - 20)),
                height: Math.round(Math.min(r.height, window.innerHeight - 20)),
                maximized: false,
            });
        }

        this._drag = null;
        this._resize = null;

        if (this._onMove) document.removeEventListener('pointermove', this._onMove);
        if (this._onUp) document.removeEventListener('pointerup', this._onUp);
        if (this._onCancel) document.removeEventListener('pointercancel', this._onCancel);

        this._onMove = null;
        this._onUp = null;
        this._onCancel = null;
    },
});
