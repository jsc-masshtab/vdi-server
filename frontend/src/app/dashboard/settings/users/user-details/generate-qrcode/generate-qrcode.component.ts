import { Component, Inject, OnDestroy, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { WaitService } from 'src/app/dashboard/common/components/single/wait/wait.service';
import { UsersService } from '../../users.service';

@Component({
  selector: 'vdi-generate-qrcode',
  templateUrl: './generate-qrcode.component.html',
  styleUrls: ['./generate-qrcode.component.scss']
})
export class GenerateQrcodeComponent implements OnInit, OnDestroy {

  private destroy: Subject<any> = new Subject<any>();

  qr = new FormControl()
  qr_accept = new FormControl(false)
  qr_uri: string = '';
  qr_secret: string = '';

  public valid: boolean = true;

  constructor(
    private waitService: WaitService,
    private dialogRef: MatDialogRef<GenerateQrcodeComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any,
    private service: UsersService
  ) { }

  ngOnInit() {
    
    this.qr.valueChanges.pipe(takeUntil(this.destroy)).subscribe((qr) => {
      if (!qr) {
        this.qr_uri = '';
        this.qr_accept.setValue(false);
      }
    });

    this.qr_accept.valueChanges.pipe(takeUntil(this.destroy)).subscribe(() => {
      this.valid = true;
    });

    this.qr.setValue(this.data.two_factor);
  }

  generateUserQrcode() {

    this.waitService.setWait(true);

    this.service.generateUserQrcode(this.data.id).pipe(takeUntil(this.destroy)).subscribe((res: any) => {

      const data = res.data.generateUserQrcode;

      this.qr_uri = data.qr_uri;
      this.qr_secret = data.secret;

      this.waitService.setWait(false);
    });
  }

  send() {
    if (this.qr_accept.value || !this.qr.value) {

      this.waitService.setWait(true);

      const params = {
        args: '$id: UUID!, $two_factor: Boolean',
        call: 'id: $id, two_factor: $two_factor',
        props: {
          id: this.data.id,
          two_factor: this.qr.value
        }
      }

      this.service.updateUser(params).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {
          this.service.getUser(this.data.id).refetch();
          this.waitService.setWait(false);
          this.dialogRef.close();
        }
      });
    } else {
      this.valid = false;
    }
  }

  ngOnDestroy() {
    this.destroy.next(null);
  }
}
