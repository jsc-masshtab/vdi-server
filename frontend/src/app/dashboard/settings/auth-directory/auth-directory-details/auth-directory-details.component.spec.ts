import { CUSTOM_ELEMENTS_SCHEMA } from '@angular/core';
import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { AuthenticationDirectoryDetailsComponent } from './auth-directory-details.component';
import { AuthenticationDirectoryService } from '../auth-directory.service';

describe('AuthenticationDirectoryDetailsComponent', () => {
  let component: AuthenticationDirectoryDetailsComponent;
  let fixture: ComponentFixture<AuthenticationDirectoryDetailsComponent>;

  let serviceStub: Partial<AuthenticationDirectoryService>;

  beforeEach(async(() => {
    serviceStub = {
      getAuthenticationDirectory(): any {
        return {
          valueChanges: of({
            data: {
              auth_dir: []
            }
          })
        };
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [AuthenticationDirectoryDetailsComponent ],
      providers: [
        {
          provide: MatDialog,
          useValue: {}
        },
        {
          provide: AuthenticationDirectoryService,
          useValue: serviceStub
        },
      ],
      schemas: [ CUSTOM_ELEMENTS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AuthenticationDirectoryDetailsComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
