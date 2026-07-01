/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { Dialog } from '@web/core/dialog/dialog';
import { rpc } from '@web/core/network/rpc';
import { onMounted, onWillUnmount, onRendered } from '@odoo/owl';
import { SelectCreateDialog } from '@web/views/view_dialogs/select_create_dialog';

function layoutKey(props) {
    return props?.title || props?.bodyId || props?.className || 'default_dialog';
}

function dbg(scope, ...args) {
    console.log(`[odoo-dialog:${scope}]`, ...args);
}

function makeDialogBehavior(options = {}) {
    const {
        targetSelector = '.modal-content',
        useFooterHandle = false,
        name = 'Dialog',
    } = options;

    return {
        setup() {
            super.setup(...arguments);
            this._drag = null;
            this._resize = null;
            this._handleObserver = null;
            dbg(name, 'setup', this.props);
            onMounted(() => this._initDialog());
            onRendered(() => this._ensureResizeHandle());
            onWillUnmount(() => this._cleanup());
        },

        async _fetchLayout(key) {
            dbg(name, '_fetchLayout', key);
            return await rpc('/odoo_dialog_user_layout/get', { key });
        },

        async _saveLayout(key, values) {
            dbg(name, '_saveLayout', key, values);
            return await rpc('/odoo_dialog_user_layout/set', { key, values });
        },

        async _resetLayout(key) {
            dbg(name, '_resetLayout', key);
            return await rpc('/odoo_dialog_user_layout/reset', { key });
        },

        async _initDialog() {
            dbg(name, '_initDialog start', this.el);

            const root = this.el;
            this.dialogEl = root?.querySelector(targetSelector) || root?.querySelector('.modal-dialog') || root;
            this.contentEl = this.dialogEl;
            dbg(name, '_initDialog found', {
                dialogEl: !!this.dialogEl,
                contentEl: !!this.contentEl,
                dialogClass: this.dialogEl?.className,
                rootClass: root?.className,
                targetSelector,
            });

            if (!this.dialogEl) return;

            this.dialogEl.classList.add('odoo-dialog-resizable');
            this.dialogEl.style.position = 'relative';
            this.dialogEl.style.margin = '0';
            this.dialogEl.style.maxWidth = 'none';
            this.dialogEl.style.overflow = 'visible';

            const key = layoutKey(this.props);
            const layout = await this._fetchLayout(key);
            const v = layout && layout[key];
            dbg(name, '_initDialog layout', { key, layout, v });

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
            this._handleObserver = new MutationObserver((mutations) => {
                dbg(name, 'mutation', mutations.map(m => ({
                    type: m.type,
                    added: m.addedNodes?.length,
                    removed: m.removedNodes?.length,
                })));
                this._ensureResizeHandle();
            });
            this._handleObserver.observe(this.dialogEl, { childList: true, subtree: false });
            dbg(name, '_initDialog observer attached');
        },

        _ensureHeaderBindings() {
            const header = this.el?.querySelector('.modal-header');
            dbg(name, '_ensureHeaderBindings', {
                header: !!header,
                className: header?.className,
            });
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
                dbg(name, '_ensureHeaderBindings added reset button');
            }
        },

        _ensureResizeHandle() {
            dbg(name, '_ensureResizeHandle start', {
                dialogEl: !!this.dialogEl,
                useFooterHandle,
                dialogClass: this.dialogEl?.className,
            });

            if (!this.dialogEl) return;

            let host = null;
            if (useFooterHandle) {
                let footer = this.dialogEl.querySelector('.modal-footer');
                dbg(name, '_ensureResizeHandle footer check', { footer: !!footer, footerClass: footer?.className });
                if (!footer) {
                    footer = document.createElement('div');
                    footer.className = 'modal-footer odoo-dialog-resize-footer';
                    footer.style.minHeight = '32px';
                    footer.style.background = 'yellow';
                    this.dialogEl.appendChild(footer);
                    dbg(name, '_ensureResizeHandle footer created');
                }
                host = footer;
            } else {
                host = this.dialogEl;
            }

            const existing = host.querySelector('.odoo-dialog-resize-handle');
            dbg(name, '_ensureResizeHandle existing', { existing: !!existing });

            if (existing) {
                this._resizeHandle = existing;
                return;
            }

            this._resizeHandle = document.createElement('div');
            this._resizeHandle.className = 'odoo-dialog-resize-handle';
            this._resizeHandle.style.background = 'red';
            this._resizeHandle.style.width = '40px';
            this._resizeHandle.style.height = '40px';
            this._resizeHandle.textContent = '↘';
            host.appendChild(this._resizeHandle);

            this._onResizeDown = (ev) => this._startResize(ev);
            this._resizeHandle.addEventListener('pointerdown', this._onResizeDown);

            dbg(name, '_ensureResizeHandle added', {
                hostClass: host?.className,
                handleClass: this._resizeHandle.className,
                handleParent: this._resizeHandle.parentElement?.className,
            });
        },

        _maximize() {
            dbg(name, '_maximize');
            this.dialogEl.style.left = '0px';
            this.dialogEl.style.top = '0px';
            this.dialogEl.style.width = '100vw';
            this.dialogEl.style.height = '100vh';
        },

        _cleanup() {
            dbg(name, '_cleanup start');
            const header = this.el?.querySelector('.modal-header');
            if (header && this._onHeaderDown) header.removeEventListener('pointerdown', this._onHeaderDown);
            if (this._resizeHandle && this._onResizeDown) this._resizeHandle.removeEventListener('pointerdown', this._onResizeDown);
            if (this._handleObserver) this._handleObserver.disconnect();
            if (this._onMove) document.removeEventListener('pointermove', this._onMove);
            if (this._onUp) document.removeEventListener('pointerup', this._onUp);
            dbg(name, '_cleanup done');
        },

        _startDrag(ev) {
            dbg(name, '_startDrag', { target: ev.target?.tagName, className: ev.target?.className });
            if (ev.target.closest('button,a,input,textarea,select')) return;
            const r = this.dialogEl.getBoundingClientRect();
            this._drag = { x: ev.clientX, y: ev.clientY, left: r.left, top: r.top };
            ev.preventDefault();
        },

        _startResize(ev) {
            dbg(name, '_startResize', { target: ev.target?.tagName, className: ev.target?.className });
            ev.preventDefault();
            ev.stopPropagation();
            ev.stopImmediatePropagation?.();
            const r = this.dialogEl.getBoundingClientRect();
            this._resize = { x: ev.clientX, y: ev.clientY, width: r.width, height: r.height };
            this._onMove = (e) => this._move(e);
            this._onUp = () => this._stop();
            document.addEventListener('pointermove', this._onMove);
            document.addEventListener('pointerup', this._onUp);
            dbg(name, '_startResize attached document listeners');
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
            dbg(name, '_stop', { drag: !!this._drag, resize: !!this._resize });
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
    };
}

patch(Dialog.prototype, makeDialogBehavior({
    targetSelector: '.modal-content',
    useFooterHandle: false,
    name: 'Dialog',
}));

patch(SelectCreateDialog.prototype, makeDialogBehavior({
    targetSelector: '.modal-content.o_select_create_dialog_content',
    useFooterHandle: true,
    name: 'SelectCreateDialog',
}));
