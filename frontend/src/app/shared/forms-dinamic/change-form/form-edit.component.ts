import { Component, Inject, OnInit, OnDestroy } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { MatDialogRef } from '@angular/material/dialog';
import { MAT_DIALOG_DATA } from '@angular/material/dialog';
import { Subscription } from 'rxjs';

import { WaitService } from '../../../core/components/wait/wait.service';


interface IData {
  post: {
    service: object,
    method: string,
    params: {
      id: string | number,
      type?: string
    }
  };
  settings: {
    entity: 'pool-details' | 'controller-details' | 'user-details',
    header: string,
    buttonAction: string,
    form: [
      {
        tag: 'input',
        type: 'number' | 'text' | 'checkbox',
        fieldName: string,
        fieldValue: string | number | boolean,
        description: string
      }
    ]
  };
  update: {
    refetch: boolean;
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

  public checkValid: boolean = false;

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
        this.formGroup.addControl(`${form[i].fieldName}`, this.fb.control(form[i].fieldValue, form[i].unrequired ? null : Validators.required));
      }
      this.init = true;
    } else {
      throw new Error('settings.form пуст');
    }
  }

  public changeCheck(field): void {
    if (field.dependName) {
      const depend = field.dependName;

      if (this.formGroup.get(field.fieldName).value) {
        depend.on.forEach((checkbox) => {
          this.formGroup.get(checkbox).setValue(true)
        })
      } else {
        depend.off.forEach((checkbox) => {
          this.formGroup.get(checkbox).setValue(false)
        })
      }
    }
  }

  public dependChecked(field): boolean {
    if (field.dependBy) {
      return this.formGroup.get(field.depend_by).value
    }
    return false;
  }

  public selectionChange(event, fieldName): void {
    this.formGroup.value[fieldName] = event.value;
  }

  public send() {
    if (this.formGroup.valid) {
      if (this.data.post && this.data.update) {
        this.waitService.setWait(true);
        this.data.post.service[this.data.post.method](this.data.post.params, this.formGroup.value).subscribe(() => {
          if (this.data.update.refetch) {
            this.data.post.service[this.data.update.method](...this.data.update.params).refetch();
            this.waitService.setWait(false);
            if (this.data.updateDepend) {
              this.data.updateDepend.service[this.data.updateDepend.method](...this.data.updateDepend.params);
            }
            this.dialogRef.close();
          } else {
            this.sub = this.data.post.service[this.data.update.method](...this.data.update.params).subscribe(() => {
              this.waitService.setWait(false);
              if (this.data.updateDepend) {
                this.data.updateDepend.service[this.data.updateDepend.method](...this.data.updateDepend.params);
              }
              this.dialogRef.close();
            });
          }
        });
      } else {
        this.waitService.setWait(true);
        this.data.post.service[this.data.post.method](this.data.post.params, this.formGroup.value).subscribe(() => {
          this.waitService.setWait(false);
          this.dialogRef.close();
        })
      }
    } else {
      this.checkValid = true;
    }
  }

  ngOnDestroy() {
    if (this.sub) {
      this.sub.unsubscribe();
    }
  }
}
