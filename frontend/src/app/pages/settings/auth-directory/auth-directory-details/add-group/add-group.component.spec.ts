import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { CUSTOM_ELEMENTS_SCHEMA, NO_ERRORS_SCHEMA } from '@angular/core';
import { MatDialogRef, MAT_DIALOG_DATA } from '@angular/material/dialog';
import { of } from 'rxjs';

import { AddGropComponent } from './add-group.component';
import { AuthenticationDirectoryService } from '../../auth-directory.service';

describe('AddGropComponent', () => {
  let component: AddGropComponent;
  let fixture: ComponentFixture<AddGropComponent>;

  let serviceStub: Partial<AuthenticationDirectoryService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getAuthenticationDirectoryGroups(): any {
        return {
          valueChanges: of({
            data: {
              auth_dir: {
                possible_ad_groups: []
              }
            }
          })
        };
      }
    };

    TestBed.configureTestingModule({
      declarations: [ AddGropComponent ],
      providers: [
        {
          provide: MatDialogRef,
          useValue: {}
        },
        {
          provide: MAT_DIALOG_DATA,
          useValue: {}
        },
        {
          provide: AuthenticationDirectoryService,
          useValue: serviceStub
        },
      ],
      schemas: [
        CUSTOM_ELEMENTS_SCHEMA,
        NO_ERRORS_SCHEMA
      ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AddGropComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
