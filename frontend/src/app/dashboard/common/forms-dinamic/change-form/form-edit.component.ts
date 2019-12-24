import { Subscription } from 'rxjs';
import { WaitService } from '../../components/single/wait/wait.service';
import { MatDialogRef } from '@angular/material';
import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
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
        type: 'number' | 'text' | 'checkbox',
        fieldName: string,
        fieldValue: string | number,
        description: string
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
    params: []
  };
}

@Component({
  selector: 'vdi-form-edit',
  templateUrl: './form-edit.component.html'
})

export class FormForEditComponent implements OnInit, OnDestroy {

  private formGroup: FormGroup;
  public init = false;
  private sub: Subscription;

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

  public changeCheck(event, fieldName): void {
    this.formGroup.value[fieldName] = event.checked;
  }

  public send() {
    if (this.data.post && this.data.update) {
      this.waitService.setWait(true);
      this.data.post.service[this.data.post.method](this.data.post.params, this.formGroup.value).subscribe(() => {
        this.sub =  this.data.post.service[this.data.update.method](...this.data.update.params).subscribe(() => {
          this.waitService.setWait(false);
          if (this.data.updateDepend) {
            this.data.updateDepend.service[this.data.updateDepend.method](...this.data.updateDepend.params);
          }
          this.dialogRef.close();
        });
      });
    } else {
      throw new Error('post || update отсутствует');
    }
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
