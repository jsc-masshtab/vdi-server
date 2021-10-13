import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { MatDialog, MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { DomSanitizer, SafeResourceUrl } from '@angular/platform-browser';
import { Subscription } from 'rxjs';

import { PoolsService, VMActions } from '../../pools.service';
import { PoolDetailMapper } from '../pool-detail.mapper';
import { RemoteData } from '../pool-details.component';
import { WaitService } from '../../../../core/wait/wait.service';
import { YesNoFormComponent } from '../../../../components/yes-no-form/yes-no-form.component';




@Component({
  selector: 'app-remote-component',
  templateUrl: './remote-component.html',
  styleUrls: ['./remote-component.scss']
})
export class RemoteComponent implements OnInit, OnDestroy{
    public data: RemoteData;
    public url: SafeResourceUrl;
    public subPool$: Subscription;
    
    constructor(
        private poolSerive: PoolsService,
        private waitService: WaitService,
        private sanitizer: DomSanitizer,
        private dialog: MatDialog,
        private dialogRef: MatDialogRef<RemoteComponent>,
        @Inject(MAT_DIALOG_DATA) data: RemoteData 
    ) { 
        this.data = data;
    }
  
    ngOnInit() {
        this.generateUrl();
      }
  
  public generateUrl(): void {
    const {pool, connectionType} = this.data;
    let url: string;
      
    switch (connectionType) {
      case 'SPICE':
        
        url = `/spice-html5/spice_auto.html?host=${pool.host}`;

        if (pool.port){
          url += `&port=${pool.port}`;
        }

        if (pool.password){
          url += `&password=${pool.password}`;
        }
        
        url += `&path=websockify?token=${pool.token}`;
        break;
      case 'VNC':
        url = `novnc/${connectionType}.html?/host=${pool.host}`;

        const prot = window.location.protocol;

        let port = 80;

        if (prot === 'https:') {
          port = 443;
        }
        if (pool.port){
          port = pool.port;
        }

        url += `&port=${port}`;

        if (pool.password){
          url += `&password=${pool.password}`;
        }
        
        url += `&path=websockify?token=${pool.token}`;
        break
      default:
        throw new Error('Method is not implemented');
    }
      
    this.url = this.sanitizer.bypassSecurityTrustResourceUrl(url);
  
  }

  public get name(): string {
    return this.data.pool.vmVerboseName;
  }
  
  public close(): void {
    this.dialogRef.close();
  }

  public refresh(): void {
    if (this.subPool$) {
      this.subPool$.unsubscribe();
    }
    this.waitService.setWait(true);   

    this.subPool$ = this.poolSerive.getPoolDetail(this.data.idPool).subscribe( (res) => {
      this.data = { pool: PoolDetailMapper.transformToClient(res.data), ...this.data };
      this.generateUrl();
      this.waitService.setWait(false);       
    })    
  }

  public manageVM(action: VMActions): void{
    switch (action) {
      case VMActions.Start:
        this.dialog.open(YesNoFormComponent, {
          disableClose: true,
          width: '500px',
          data: {
            form: {
              header: 'Подтверждение действия',
              question: 'Включить ВМ?',
              button: 'Выполнить'
            },
            request: {
              service: this.poolSerive,
              action: 'manageVM',
              body: {
                id: this.data.idPool,
                action: VMActions.Start,
              }
            }
          }
        })
        break;
      case VMActions.Suspend:
        this.dialog.open(YesNoFormComponent, {
          disableClose: true,
          width: '500px',
          data: {
            form: {
              header: 'Подтверждение действия',
              question: 'Приостановить ВМ?',
              button: 'Выполнить'
            },
            request: {
              service: this.poolSerive,
              action: 'manageVM',
              body: {
                id: this.data.idPool,
                action: VMActions.Suspend,
              }
            }
          }
        })
        break;
      case VMActions.Shutdown:
        this.dialog.open(YesNoFormComponent, {
          disableClose: true,
          width: '500px',
          data: {
            form: {
              header: 'Подтверждение действия',
              question: 'Выключить ВМ?',
              button: 'Выполнить'
            },
            request: {
              service: this.poolSerive,
              action: 'manageVM',
              body: {
                id: this.data.idPool,
                action: VMActions.Shutdown,
              }
            }
          }
        })
        break;
      case VMActions.Reboot:
        this.dialog.open(YesNoFormComponent, {
          disableClose: true,
          width: '500px',
          data: {
            form: {
              header: 'Подтверждение действия',
              question: 'Перезагрузить ВМ?',
              button: 'Выполнить'
            },
            request: {
              service: this.poolSerive,
              action: 'manageVM',
              body: {
                id: this.data.idPool,
                action: VMActions.Reboot,
              }
            }
          }
        })
        break;
      default:
        throw Error('Something went wrong')
        break;
    }
  }

  public ngOnDestroy(): void {
    if (this.subPool$) {
      this.subPool$.unsubscribe();
    }
  }

}
