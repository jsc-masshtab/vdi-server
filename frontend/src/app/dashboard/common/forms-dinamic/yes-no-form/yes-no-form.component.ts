import { Component, OnInit, Inject } from '@angular/core';
import { WaitService } from '../../components/single/wait/wait.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material';
import { Observable, Subject } from 'rxjs';

@Component({
  selector: 'vdi-yes-no-form',
  templateUrl: './yes-no-form.component.html',
  styleUrls: ['./yes-no-form.component.scss']
})
export class YesNoFormComponent implements OnInit {

  public init = false

  constructor(
    private waitService: WaitService,
    private dialogRef: MatDialogRef<YesNoFormComponent>,
    @Inject(MAT_DIALOG_DATA) public data: any
  ) {}

  ngOnInit() {
    this.init = true
  }

  send() {
    const request = { ...this.data.request }

    this.waitService.setWait(true);

    request.service[request.action](request.body).subscribe(() => {
      this.waitService.setWait(false);
      this.dialogRef.close();
    })
  }

}
