
import { WaitService } from '../../single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';

interface IData {
  post: {
    service: object,
    method: string,
    params: {
      id: string | number
    }
  };
  settings: {
    entity: string,
    name: string,
    header: string,
    buttonAction: string
  };
  update: {
    method: string;
    params: {
      id: string | number,
      type?: string
    },
  };
}

@Component({
  selector: 'vdi-form-edit',
  templateUrl: './form-edit.component.html'
})

export class FormForEditComponent implements OnInit {

  private name: string = '';

  constructor(private waitService: WaitService,
              private dialogRef: MatDialogRef<FormForEditComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData
  ) {}

  ngOnInit() {
    this.name = this.data.settings.name;
  }

  public send() {
    this.waitService.setWait(true);
    this.data.post.service[this.data.post.method](this.data.post.params, { newName: this.name }).subscribe(() => {
      this.waitService.setWait(false);
      this.data.post.service[this.data.update.method](this.data.update.params).subscribe(() => {
        this.waitService.setWait(false);
      });
      this.dialogRef.close();
    });
  }
}
