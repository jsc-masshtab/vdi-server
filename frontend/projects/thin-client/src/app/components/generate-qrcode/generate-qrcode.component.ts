import { Component, OnDestroy, OnInit } from '@angular/core';
import { FormControl } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';

import { Subject } from 'rxjs';
import { takeUntil } from 'rxjs/operators';
import { UserService } from '../../core/services/user.service';
import { WaitService } from '../../core/wait/wait.service';
import { QRCodeService } from './qrcode.service';




@Component({
  selector: 'tc-generate-qrcode',
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
    public userSerivce: UserService,
    private qrcodeService: QRCodeService 
  ) { }

  ngOnInit() {
    this.userSerivce.getUserData().subscribe((res) => {
      const data = res.data.user;
      this.qr.setValue(data.two_factor);

    })
    this.qr.valueChanges.pipe(takeUntil(this.destroy)).subscribe((qr) => {
      if (!qr) {
        this.qr_uri = '';
        this.qr_accept.setValue(false);
      }
    });

    this.qr_accept.valueChanges.pipe(takeUntil(this.destroy)).subscribe(() => {
      this.valid = true;
    });

  }

  generateUserQrcode() {

    this.waitService.setWait(true);

    this.qrcodeService.generateQRCode().pipe(takeUntil(this.destroy)).subscribe((res) => {

      const data = res.data;

      this.qr_uri = data.qr_uri;
      this.qr_secret = data.secret;

      this.waitService.setWait(false);
    });
  }

  send() {
    if (this.qr_accept.value || !this.qr.value) {

      this.waitService.setWait(true);

      this.userSerivce.updateUserData(this.qr.value).pipe(takeUntil(this.destroy)).subscribe((res) => {
        if (res) {
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
