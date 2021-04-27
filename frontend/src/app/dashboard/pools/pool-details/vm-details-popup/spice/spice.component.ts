/* eslint-disable @typescript-eslint/consistent-type-assertions */

/* eslint-disable prefer-const, max-len, no-console, @typescript-eslint/member-ordering, @typescript-eslint/unbound-method */

import {
  Component,
  Input,
  Output,
  EventEmitter,
  AfterViewInit,
  OnChanges,
  OnDestroy
} from '@angular/core';

import * as SpiceHtml5 from 'src/spice/src/main.js'

@Component({
  selector: 'spice-widget',
  styleUrls: ['./spice.component.scss'],
  templateUrl: './spice.component.html'
})

export class SpiceComponent implements AfterViewInit, OnChanges, OnDestroy {

  constructor() { }

  @Input() domain: any = {};
  @Input() resize: any;
  @Output() isRoute = new EventEmitter<boolean>();

  nav: string;
  init = true;
  url = '';
  sc: any;

  device: any;

  routeToInformation() {
    this.isRoute.emit();
  }

  ngAfterViewInit() {
    this.load();

    setTimeout(() => {
      this.refresh();
    }, 1000);
  }

  ngOnChanges() {
    if (this.sc) {
      SpiceHtml5.resize_helper(this.sc);
    }
  }

  refresh() {
    this.load();
  }

  private load(): void {
    this.init = false;

    this.disconnect();

    const spice = this.domain.spice_connection
    this.url = `${spice.connection_url}`.replace(':', '&port=');
    this.connect(undefined);
    this.init = true;
  }

  spice_set_cookie(name, value, days) {
    let date; let expires;
    date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    expires = '; expires=' + date.toGMTString();
    document.cookie = name + '=' + value + expires + '; path=/';
  }
  spice_query_var(name, defvalue) {
    const match = RegExp('[?&]' + name + '=([^&]*)')
      .exec(this.url);
    return match ?
      decodeURIComponent(match[1].replace(/\+/g, ' '))
      : defvalue;
  }

  spice_error(e) {

    this.disconnect();

    if (e !== undefined && e.message === 'Permission denied.') {
      this.refresh();
    }
  }

  connect(password) {
    let host; let port; let scheme = 'ws://'; let uri;

    host = this.spice_query_var('host', window.location.hostname);

    let default_port: number;

    if (!default_port) {
      if (window.location.protocol === 'http:') {
        default_port = 80;
      } else if (window.location.protocol === 'https:') {
        default_port = 443;
      }
    }

    port = this.spice_query_var('port', default_port);
    if (window.location.protocol === 'https:') {
      scheme = 'wss://';
    }

    if (password === undefined) {
      password = this.spice_query_var('password', '');
    }

    const path = this.spice_query_var('path', 'websockify');

    if ((!host) || (!port)) {
      console.log('must specify host and port in URL');
      return;
    }

    if (this.sc) {
      this.sc.stop();
    }

    uri = scheme + host + ':' + port;

    if (path) {
      uri += path[0] === '/' ? path : ('/' + path);
    }

    try {
      this.sc = new SpiceHtml5.SpiceMainConn({
        uri, screen_id: 'spice-screen-' + this.domain.id,
        spice_area: this.domain.id, password, onerror: this.spice_error(this), onagent: this.agent_connected
      });
    } catch (e) {
      this.disconnect();
    }

  }

  disconnect(): void {
    /* if (this.sc) {
      this.sc.stop();
    }

    window.removeEventListener('resize', SpiceHtml5.handle_resize, false); */
  }

  agent_connected(e) {
    const context = e;
    (window as any).spice_connection = e;
    SpiceHtml5.resize_helper(e);

    window.addEventListener('resize', SpiceHtml5.handle_resize);

    if ((window as any).File && (window as any).FileReader && (window as any).FileList && (window as any).Blob) {
      const spice_xfer_area = document.createElement('div');
      spice_xfer_area.setAttribute('id', 'spice-xfer-area');
      document.getElementById('loading').appendChild(spice_xfer_area);
      document.getElementById('spice-area-' + context.spice_area).addEventListener('dragover', SpiceHtml5.handle_file_dragover, false);
      document.getElementById('spice-area-' + context.spice_area).addEventListener('drop', SpiceHtml5.handle_file_drop, false);
    } else {
      console.log('File API is not supported');
    }
  }

  ngOnDestroy() {
    this.disconnect();
  }

  ctrlAltDelete() {
    SpiceHtml5.sendCtrlAltDel(this.sc);
  }

  ctrlAltF(fkey) {
    if (fkey[0] === 'DEL') {
      this.ctrlAltDelete();
    }
    if (fkey[0] === 'empty') {
      return;
    } else {
      SpiceHtml5.sendCtrlAltF(this.sc, fkey[0]);
      setTimeout(() => {
        this.refresh();
      }, 50);
    }
  }

  addUsb() {
    this.device = (navigator as any).usb.requestDevice({
      filters: []
    });
  }

  showUsb() {
    new Promise((resolve) => {
      resolve((navigator as any).usb.getDevices());
    }).then((device: any) => {


      new Promise((resolve) => {
        resolve(device[0].open());
      }).then((e: any) => {
        console.log(e);
      });
    });
  }

  newTabTerminal(): void {
    window.open(window.location.origin + this.url);
    localStorage.setItem('domain', this.domain.verbose_name);
    localStorage.setItem('id', this.domain.id);
  }

  fullScreen() {
    document.getElementById('spice-area-' + this.domain.id).requestFullscreen();
  }

}
