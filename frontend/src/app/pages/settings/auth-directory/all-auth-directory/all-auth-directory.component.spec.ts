import { NO_ERRORS_SCHEMA } from '@angular/core';
import { waitForAsync, ComponentFixture, TestBed } from '@angular/core/testing';
import { RouterTestingModule } from '@angular/router/testing';
import { MatDialog } from '@angular/material/dialog';
import { of } from 'rxjs';

import { AuthenticationDirectoryComponent } from './all-auth-directory.component';
import { AuthenticationDirectoryService } from '../auth-directory.service';

describe('AuthenticationDirectoryComponent', () => {
  let component: AuthenticationDirectoryComponent;
  let fixture: ComponentFixture<AuthenticationDirectoryComponent>;

  let serviceStub: Partial<AuthenticationDirectoryService>;

  beforeEach(waitForAsync(() => {
    serviceStub = {
      getAllAuthenticationDirectory(): any {
        return {
          valueChanges: of({
            data: {
              auth_dirs: []
            }
          })
        };
      },
      paramsForGetAuthenticationDirectory: {
        spin: false
      }
    };

    TestBed.configureTestingModule({
      imports: [ RouterTestingModule ],
      declarations: [AuthenticationDirectoryComponent ],
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
      schemas: [ NO_ERRORS_SCHEMA ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(AuthenticationDirectoryComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
