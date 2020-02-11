/* tslint:disable:no-unused-variable */
import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { AuthenticationDirectoryDetailsComponent } from './auth-directory-details.component';

describe('AuthDirectoryDetailsComponent', () => {
  let component: AuthenticationDirectoryDetailsComponent;
  let fixture: ComponentFixture<AuthenticationDirectoryDetailsComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [AuthenticationDirectoryDetailsComponent ]
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
