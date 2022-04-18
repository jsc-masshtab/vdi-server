import { Component, OnInit, OnDestroy } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialog } from '@angular/material/dialog';
import { ActivatedRoute, ParamMap, Router } from '@angular/router';
import { Subscription } from 'rxjs';

import { WebsocketService } from '../../../core/services/websock.service';
import { WaitService } from '../../../core/wait/wait.service';
import { PoolsService } from '../pools.service';
import { IPoolDetailClient, PoolDetailMapper } from './pool-detail.mapper';
import { RemoteComponent } from './remote-component/remote-component';

export type RemoteData = {
  pool: IPoolDetailClient,
  connectionType: string,
  idPool: string,
  isFullscreenActive: boolean
}
@Component({
  selector: 'app-pool-details',
  templateUrl: './pool-details.component.html',
  styleUrls: ['./pool-details.component.scss']
})

export class PoolDetailsComponent implements OnInit, OnDestroy {
  private subPool$: Subscription;
  private socketSub$: Subscription;
  private idPool: string;
  public isFullscreenActive: boolean = false;
  public notifications: number = 0;
  public host: boolean = false;
  public pool: IPoolDetailClient;
  public connectionTypes: string[];
  public connectionControl: FormControl = new FormControl();
  public collectionDetails: any[] = [
    {
      title: 'Название',
      property: 'vmVerboseName',
      type: 'string',
    },
    {
      title: 'Хост',
      property: 'host',
      type: 'string',
    },
    {
      title: 'Адрес',
      property: 'vmControllerAddress',
      type: 'pool_type'
    },
    {
      title: 'Порт',
      property: 'port',
      type: 'string',

    },
    {
      title: 'Список разрешений',
      property: 'permissions',
      type: 'array'
    },
  ];

  public  menuActive: string = 'info';

  constructor(private activatedRoute: ActivatedRoute,
              private router: Router,
              private poolService: PoolsService,
              private waitService: WaitService,
              private ws: WebsocketService,
              private dialog: MatDialog) { }

  ngOnInit() {
    
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      
      this.idPool = param.get('id');
      if (history.state.data) {
        this.connectionTypes = history.state.data;
        this.connectionControl = new FormControl(this.connectionTypes[0]);
        this.getPool();
      } else {
        this.close();
      }
    });
    
    this.listenSockets()

  }

  public getPool(): void {
    if (this.subPool$) {
      this.subPool$.unsubscribe();
    }

    this.waitService.setWait(true);   
    this.host = false;

    this.subPool$ = this.poolService.getPoolDetail(this.idPool).subscribe((res: any) => {
      if (res.data){
        this.pool =  PoolDetailMapper.transformToClient(res.data);
        this.host = true;
        this.ws.init(this.pool.vmId);
      }  
      
      if (res.errors) {
        this.close();
      }

      this.waitService.setWait(false);

    })
  }

  public routeTo(route: string): void {
    this.menuActive = route;
  }

  public close(): void  {
    this.router.navigateByUrl('pages/pools');
  }


  public clickConnect(): void  {    
    const remoteData: RemoteData = {
      pool: this.pool,
      connectionType: this.connectionControl.value,
      idPool: this.idPool,
      isFullscreenActive: this.isFullscreenActive
    }

    this.dialog.open(RemoteComponent, {
      disableClose: true,
      maxWidth: '90vw',
      maxHeight: '90vh',
      height: '100%',
      width: '100%',
      data: remoteData
    });
  
  }

  public ngOnDestroy() {
    if (this.subPool$) {
      this.subPool$.unsubscribe();
    }
  }

  private listenSockets() {
    if (this.socketSub$) {
      this.socketSub$.unsubscribe();
    }

    this.socketSub$ = this.ws.event$.subscribe((message: any) => {
      
      if (message.msg_type === 'text_msg' ) {
        this.notifications++;
      }         
    });
  }

  public clearNotifications(): void {
    this.notifications = 0;
  }

}
