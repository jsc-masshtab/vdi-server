
import { WaitService } from '../../single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnInit } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';

interface IData {
  entity: {
    entity: string,
    name: string,
    id: string,
    service: object,
    method: string,
    params: {
      id: string | number
    }
  };
  settings: {
    header: string,
    buttonAction: string
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
    this.name = this.data.entity.name;
    console.log(this.data, typeof this.data.entity.service);
  }

  public send() {
    this.waitService.setWait(true);
    this.data.entity.service[this.data.entity.method](this.data.entity.params.id, this.name).subscribe(() => {
      this.waitService.setWait(false);
      // this.poolService.getPool(this.data.idPool, this.data.typePool).subscribe(() => {
      //   this.waitService.setWait(false);
      // });
      this.dialogRef.close();
    });
  }
}
