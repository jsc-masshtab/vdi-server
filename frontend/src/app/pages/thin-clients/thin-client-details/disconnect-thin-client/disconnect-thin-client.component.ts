import { Component, Inject, OnDestroy } from '@angular/core';
import { Subject, of } from 'rxjs';
import { WaitService } from 'src/app/core/components/wait/wait.service';
import { ThinClientsService } from '../../thin-clients.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Router } from '@angular/router';
import { takeUntil, concatMap, delay } from 'rxjs/operators';

@Component({
  selector: 'vdi-disconnect-thin-client',
  templateUrl: './disconnect-thin-client.component.html',
  styleUrls: ['./disconnect-thin-client.component.scss']
})
export class DisconnectThinClientComponent implements OnDestroy {

  private destroy: Subject<any> = new Subject<any>();

  constructor(private service: ThinClientsService,
              private waitService: WaitService,
              private dialogRef: MatDialogRef<ThinClientsService>,
              @Inject(MAT_DIALOG_DATA) public data: any,
              private router: Router) { }


  public send() {
    this.waitService.setWait(true);
    this.service.disconnectThinClient(this.data.conn_id).pipe(concatMap(item => of(item).pipe(delay(1000)))).subscribe((res) => {
      if (res) {
        this.service.getThinClients().valueChanges.pipe(takeUntil(this.destroy)).subscribe(() => {
          this.waitService.setWait(false);
          this.dialogRef.close();
          this.router.navigateByUrl('/pages/clients/session');
        });
      }
    });
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }

}
