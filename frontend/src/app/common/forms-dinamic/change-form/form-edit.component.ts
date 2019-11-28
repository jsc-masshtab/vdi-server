import { WaitService } from '../../components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnInit  } from '@angular/core';
import { MAT_DIALOG_DATA } from '@angular/material';
import { FormBuilder, FormGroup } from '@angular/forms';


interface IData {
  post: {
    service: object,
    method: string,
    params: {
      id: string | number,
      type: string
    }
  };
  settings: {
    entity: 'pool-details',
    header: string,
    buttonAction: string,
    form: [
      {
        tag: 'input',
        type: 'number' | 'text',
        fieldName: string,
        fieldValue: string | number
      }
    ]
  };
  update: {
    method: string;
    params: [],
  };
  updateDepend?: {
    method: string;
    service: object;
  };
}

@Component({
  selector: 'vdi-form-edit',
  templateUrl: './form-edit.component.html'
})

export class FormForEditComponent implements OnInit {

  private formGroup: FormGroup;
  public init = false;

  constructor(private waitService: WaitService,
              private dialogRef: MatDialogRef<FormForEditComponent>,
              @Inject(MAT_DIALOG_DATA) public data: IData,
              private fb: FormBuilder
  ) { this.formGroup = this.fb.group({}); }

  ngOnInit() {
    this.createFormGroup();
  }

  private createFormGroup() {
    let form;
    if (this.data.settings.form) {
      form = this.data.settings.form;
    } else {
      throw new Error('settings.form отсутствует');
    }
    if (form.length) {
      for (let i = 0; i < form.length; i++) {
        this.formGroup.addControl(`${form[i].fieldName}`, this.fb.control(form[i].fieldValue));
      }
      this.init = true;
    } else {
      throw new Error('settings.form пуст');
    }
  }

  public send() {
    if (this.data.post && this.data.update) {
      this.waitService.setWait(true);
      this.data.post.service[this.data.post.method](this.data.post.params, this.formGroup.value).subscribe(() => {
        console.log(this.data.update.method, this.data.update.params);
        this.data.post.service[this.data.update.method](...this.data.update.params).subscribe(() => {
          this.waitService.setWait(false);
          if (this.data.updateDepend) {
            this.data.updateDepend.service[this.data.updateDepend.method]().subscribe();
          }
        });
        this.dialogRef.close();
      });
    } else {
      throw new Error('post || update отсутствует');
    }
  }
}
