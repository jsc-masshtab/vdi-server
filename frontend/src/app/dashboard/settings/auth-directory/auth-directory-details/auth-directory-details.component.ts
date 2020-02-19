import { AddMappingComponent } from './add-mapping/add-mapping.component';
import { Component, OnInit, OnDestroy } from '@angular/core';
import { AuthenticationDirectoryService } from '../auth-directory.service';
import { Subscription } from 'rxjs';
import { ParamMap, ActivatedRoute, Router } from '@angular/router';
import { FormForEditComponent } from 'src/app/dashboard/common/forms-dinamic/change-form/form-edit.component';
import { MatDialog } from '@angular/material';
import { RemoveAuthenticationDirectoryComponent } from './remove-auth-directory/remove-auth-directory.component';

@Component({
  selector: 'auth-directory-details',
  templateUrl: './auth-directory-details.component.html',
  styleUrls: ['./auth-directory-details.component.scss']
})
export class AuthenticationDirectoryDetailsComponent implements OnInit, OnDestroy {

  getAuthenticationDirectorySub: Subscription;

  id: string;
  AuthenticationDirectory: any;

  testing: boolean = false;
  tested: boolean = false;
  connected: boolean = false;
  public menuActive: string = 'info';
  public host: boolean = false;

  public collection: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'openEditForm',
      form: {
        tag: 'input',
        type: 'text'
      }
    },
    {
      title: 'Domain name',
      property: 'domain_name',
      type: 'string',
      edit: 'openEditForm',
      form: {
        tag: 'input',
        type: 'text'
      }
    },
    {
      title: 'Directory url',
      property: 'directory_url',
      type: 'string',
      edit: 'openEditForm',
      form: {
        tag: 'input',
        type: 'text'
      }
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string',
      edit: 'openEditForm',
      form: {
        tag: 'textarea',
        type: 'text'
      }
    }
  ];

  public collection_mapping: object[] = [
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'openEditForm'
    },
    {
      title: 'Описание',
      property: 'description',
      type: 'string',
      edit: 'openEditForm'
    },
    {
      title: 'Тип атрибута службы каталогов',
      property: 'value_type',
      type: 'string',
      edit: 'openEditForm'
    },
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'openEditForm'
    },
    {
      title: 'Название',
      property: 'verbose_name',
      type: 'string',
      edit: 'openEditForm'
    }
  ];

  constructor(private service: AuthenticationDirectoryService, private activatedRoute: ActivatedRoute, public dialog: MatDialog,
              private router: Router) { }

  ngOnInit() {
    this.activatedRoute.paramMap.subscribe((param: ParamMap) => {
      this.id = param.get('id');
      this.getAuthenticationDirectory();
     });
  }

  public getAuthenticationDirectory(): void {
    this.host = false;
    if (this.getAuthenticationDirectorySub) {
      this.getAuthenticationDirectorySub.unsubscribe();
    }

    this.getAuthenticationDirectorySub = this.service.getAuthenticationDirectory(this.id)
      .subscribe((data) => {
        this.host = true;
        this.AuthenticationDirectory = data.auth_dir;
      });
  }

  public edit(line: any) {
    this[line.edit](line);
  }

  public openEditForm(options): void {
    let gqlType: string = 'String';

    if (options.form.gqlType) {
      gqlType = options.form.gqlType;
    }

    this.dialog.open(FormForEditComponent, {
      width: '500px',
      data: {
        post: {
          service: this.service,
          method: 'updateAuthenticationDirectory',
          params: {
            args: `$id: UUID!, $${options.property}: ${gqlType}`,
            call: `id: $id, ${options.property}: $${options.property}`,
            props: {
              id: this.id,
            }
          }
        },
        settings: {
          entity: 'auth-directory-details',
          header: `Изменение свойства "${options.title}"`,
          buttonAction: 'Изменить',
          form: [{
            tag: options.form['tag'],
            type: options.form['type'],
            fieldName: options.property,
            fieldValue: this.AuthenticationDirectory[options.property],
            description: options.form['description'] || ''
          }]
        },
        update: {
          method: 'getAuthenticationDirectory',
          params: [
            this.id
          ]
        }
      }
    });
  }

  public testAuthDir(): void {
    this.testing = true;
    this.service.testAuthenticationDirectory({
        id: this.id,
      })
      .subscribe((data) => {
        setTimeout(() => {
          this.testing = false;
          this.tested = true;
          this.connected = data.testAuthDir.ok;
        }, 1000);

        setTimeout(() => {
          this.tested = false;
        }, 5000);
      }, () => {
          this.testing = false;
          this.tested = false;
      });
  }

  public remove(): void {
    this.dialog.open(RemoveAuthenticationDirectoryComponent, {
      width: '500px',
      data: {
        id: this.id,
        item: this.AuthenticationDirectory
      }
    });
  }

  public addMatch() {
    this.dialog.open(AddMappingComponent, {
      width: '500px',
      data: {
        id: this.id
      }
    });
  }

  public close() {
    this.router.navigate(['pages/settings/auth-directory']);
  }

  public routeTo(route: string): void {
    if (route === 'info') {
      this.menuActive = 'info';
    }
    if (route === 'match') {
      this.menuActive = 'match';
    }
  }

  ngOnDestroy() {
    if (this.getAuthenticationDirectorySub) {
      this.getAuthenticationDirectorySub.unsubscribe();
    }
  }
}
