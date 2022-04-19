import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { Subscription } from 'rxjs';
import { map } from 'rxjs/operators';

import { WebsocketService } from '@app/core/services/websock.service';
import { ThinClientsService } from '../thin-clients.service';
import { DisconnectThinClientComponent } from './disconnect-thin-client/disconnect-thin-client.component';
import { ThinClientColections } from './collections';

@Component({
  selector: 'vdi-thin-client-details',
  templateUrl: './thin-client-details.component.html',
  styleUrls: ['./thin-client-details.component.scss']
})
export class ThinClientDetailsComponent extends ThinClientColections implements OnInit, OnDestroy {

  public host: boolean = false;

  @ViewChild('messenger', { static: false }) messenger: ElementRef;

  private sub: Subscription;
  private socketSub: Subscription;

  id: string;
  entity: any;

  message = new FormControl('')
  messages: any[] = []

  menuActive: string = 'info';

  constructor(
    private service: ThinClientsService,
    private activatedRoute: ActivatedRoute,
    private router: Router,
    public dialog: MatDialog,
    private ws: WebsocketService
  ) {
    super();
  }

  ngOnInit() {
    
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.id = param.get('id');
      this.listenSockets();
      this.getThinClient();

      this.messages = [];
    });
  }

  public getThinClient() {
    if (this.sub) {
      this.sub.unsubscribe();
    }

    this.host = false;

    this.sub = this.service.getThinClient({ conn_id: this.id })
      .valueChanges.pipe(map((data: any) => data.data['thin_client']))
      .subscribe((data) => {
        this.entity = data;
        this.host = true;
      },
      () => {
        this.host = true;
      });
  }

  private listenSockets(): void {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }

    this.socketSub = this.ws.stream('/users/').subscribe((message: any) => {
      if (message.msg_type === 'text_msg' && message.sender_id === this.entity.user_id) {
        this.messages.push({
          sender: message.sender_name,
          self: false,
          text: message.message,
          time: new Date().toLocaleTimeString()
        })

        if (this.messenger) {
          setTimeout(() => {
            this.messenger.nativeElement.scrollTop = this.messenger.nativeElement.scrollHeight
          })
        }
      }
    });
  }

  public routeTo(route: string): void {
    this.menuActive = route;
  }

  public disconnect(): void {
    this.dialog.open(DisconnectThinClientComponent, {
      disableClose: true,
      width: '500px',
      data: this.entity
    });
  }

  public sendMessage(): void {

    const message = this.message.value
    this.messages.push({
      sender: 'Вы',
      self: true,
      text: message,
      time: new Date().toLocaleTimeString()
    })

    this.message.setValue('')   

    setTimeout(() => {
      this.messenger.nativeElement.scrollTop = this.messenger.nativeElement.scrollHeight
    })
    
    this.service.sendMessageToThinClient(this.entity.user_id, message).subscribe()
  }

  keyEvent(e: KeyboardEvent) {
    if (e.key === 'Enter' && e.ctrlKey) {
      this.sendMessage();
    }
  }

  public close(): void {
    this.router.navigate(['pages/clients/session/']);
  }

  ngOnDestroy(): void {
    if (this.socketSub) {
      this.socketSub.unsubscribe();
    }
  }
}
