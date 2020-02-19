import { WaitService } from '../../../../common/components/single/wait/wait.service';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material';
import { Component, OnInit, Inject } from '@angular/core';
import { AuthenticationDirectoryService } from '../../auth-directory.service';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';

interface IData {
  id: string;
}


@Component({
  selector: 'vdi-add-mapping',
  templateUrl: './add-mapping.component.html'
})

export class AddMappingComponent implements OnInit {

  public form: FormGroup;
  public checkValid: boolean = false;

  public pending = {
    groups: false
  };

  public groups: [] = [];


  private initForm(): void {
    this.form = this.fb.group({
      verbose_name: ['', Validators.required],
      description: '',
      value_type: '',
      groups: ['', Validators.required],
      priority: '',
      values: ['', Validators.required]
    });
  }

  constructor(private service: AuthenticationDirectoryService,
              private dialogRef: MatDialogRef<AddMappingComponent>,
              private fb: FormBuilder,
              private waitService: WaitService,
              @Inject(MAT_DIALOG_DATA) public data: IData) {
                this.initForm();
              }

  ngOnInit() {
    this.getGroups();
  }

  public send() {
    console.log(this.form.value);
    this.checkValid = true;
    if (this.form.status === 'VALID') {
      this.waitService.setWait(true);
      this.service.addAuthDirMapping(this.form.value, this.data.id).subscribe(() => {
        this.service.getAuthenticationDirectory(this.data.id).subscribe(() => {
          this.dialogRef.close();
          this.waitService.setWait(false);
        });
      });
    }
  }

  private getGroups(): void  {
    this.pending.groups = true;
    this.service.getGroups().valueChanges
    .subscribe( (data) => {
      this.groups = data.data['groups'];
      this.pending.groups = false;
    });
  }


}





